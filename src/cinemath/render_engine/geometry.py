"""Clip lines / planes to axis boxes for system-of-equations visuals."""

from __future__ import annotations

import math
from typing import Sequence


Point2 = tuple[float, float]
Point3 = tuple[float, float, float]


def clip_line_to_rect(
    a: float,
    b: float,
    c: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    *,
    tol: float = 1e-9,
) -> tuple[Point2, Point2] | None:
    """Clip the line ``a x + b y = c`` to the closed rectangle; return endpoints."""
    if abs(a) < tol and abs(b) < tol:
        return None

    hits: list[Point2] = []

    def _add(x: float, y: float) -> None:
        if x0 - tol <= x <= x1 + tol and y0 - tol <= y <= y1 + tol:
            xx = min(max(x, x0), x1)
            yy = min(max(y, y0), y1)
            for px, py in hits:
                if abs(px - xx) < 1e-6 and abs(py - yy) < 1e-6:
                    return
            hits.append((xx, yy))

    if abs(b) > tol:
        _add(x0, (c - a * x0) / b)
        _add(x1, (c - a * x1) / b)
    if abs(a) > tol:
        _add((c - b * y0) / a, y0)
        _add((c - b * y1) / a, y1)

    if len(hits) < 2:
        return None
    if len(hits) == 2:
        return hits[0], hits[1]

    # Corners can yield >2 hits; keep the farthest pair.
    best_i, best_j, best_d = 0, 1, -1.0
    for i in range(len(hits)):
        for j in range(i + 1, len(hits)):
            dx = hits[i][0] - hits[j][0]
            dy = hits[i][1] - hits[j][1]
            dist = dx * dx + dy * dy
            if dist > best_d:
                best_d = dist
                best_i, best_j = i, j
    return hits[best_i], hits[best_j]


def plane_box_polygon(
    a: float,
    b: float,
    c: float,
    d: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    *,
    tol: float = 1e-9,
) -> list[Point3]:
    """Intersection polygon of plane ``a x + b y + c z = d`` with an axis-aligned box."""
    if abs(a) < tol and abs(b) < tol and abs(c) < tol:
        return []

    edges: list[tuple[Point3, Point3]] = [
        ((x0, y0, z0), (x1, y0, z0)),
        ((x0, y1, z0), (x1, y1, z0)),
        ((x0, y0, z1), (x1, y0, z1)),
        ((x0, y1, z1), (x1, y1, z1)),
        ((x0, y0, z0), (x0, y1, z0)),
        ((x1, y0, z0), (x1, y1, z0)),
        ((x0, y0, z1), (x0, y1, z1)),
        ((x1, y0, z1), (x1, y1, z1)),
        ((x0, y0, z0), (x0, y0, z1)),
        ((x1, y0, z0), (x1, y0, z1)),
        ((x0, y1, z0), (x0, y1, z1)),
        ((x1, y1, z0), (x1, y1, z1)),
    ]

    hits: list[Point3] = []
    for p0, p1 in edges:
        dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        denom = a * dx + b * dy + c * dz
        if abs(denom) < tol:
            continue
        t = (d - (a * p0[0] + b * p0[1] + c * p0[2])) / denom
        if t < -tol or t > 1 + tol:
            continue
        t = min(max(t, 0.0), 1.0)
        pt = (p0[0] + t * dx, p0[1] + t * dy, p0[2] + t * dz)
        if not any(
            abs(pt[0] - q[0]) < 1e-6 and abs(pt[1] - q[1]) < 1e-6 and abs(pt[2] - q[2]) < 1e-6
            for q in hits
        ):
            hits.append(pt)

    if len(hits) < 3:
        return []
    return _order_planar(hits, (a, b, c))


def _order_planar(points: Sequence[Point3], normal: Point3) -> list[Point3]:
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    cz = sum(p[2] for p in points) / len(points)
    nx, ny, nz = normal
    nlen = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    nx, ny, nz = nx / nlen, ny / nlen, nz / nlen

    # Orthonormal frame in the plane.
    if abs(nx) < 0.9:
        tx, ty, tz = 1.0, 0.0, 0.0
    else:
        tx, ty, tz = 0.0, 1.0, 0.0
    ux, uy, uz = _cross(nx, ny, nz, tx, ty, tz)
    ulen = math.sqrt(ux * ux + uy * uy + uz * uz) or 1.0
    ux, uy, uz = ux / ulen, uy / ulen, uz / ulen
    vx, vy, vz = _cross(nx, ny, nz, ux, uy, uz)

    ranked: list[tuple[float, Point3]] = []
    for p in points:
        dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
        ang = math.atan2(dx * vx + dy * vy + dz * vz, dx * ux + dy * uy + dz * uz)
        ranked.append((ang, p))
    ranked.sort(key=lambda item: item[0])
    return [p for _, p in ranked]


def _cross(
    ax: float, ay: float, az: float, bx: float, by: float, bz: float
) -> tuple[float, float, float]:
    return (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
