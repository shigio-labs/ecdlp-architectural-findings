"""Ghost-aware pebbling approximation search.

This is a relaxed model intended for Sprint 2 exploration only.
It extends black-pebble search with a second token type ("ghost") and a cap
on ghost tokens. Ghost semantics here are intentionally simplified and should
be read as an upper-bound feasibility probe, not a faithful spooky-pebbling
simulation.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .pebble_search import PebbleTree, build_balanced_binary_tree


@dataclass(frozen=True)
class GhostSearchResult:
    possible: bool
    min_steps_compute_root: int | None
    min_steps_compute_uncompute: int | None
    visited_compute: int
    visited_full: int
    cutoff_hit_compute: bool
    cutoff_hit_full: bool


def _iter_bits(mask: int):
    while mask:
        lsb = mask & -mask
        yield lsb.bit_length() - 1
        mask ^= lsb


def _valid_state(solid: int, ghost: int) -> bool:
    return (solid & ghost) == 0


def _bfs_compute_root_relaxed(
    tree: PebbleTree,
    solid_cap: int,
    ghost_cap: int,
    *,
    max_visited: int | None,
) -> tuple[int | None, int, bool]:
    start = (0, 0)
    goal_bit = 1 << tree.root
    q = deque([(start, 0)])
    seen = {start}
    cutoff_hit = False

    while q:
        (solid, ghost), dist = q.popleft()
        live = solid | ghost
        if live & goal_bit:
            return dist, len(seen), cutoff_hit

        if max_visited is not None and len(seen) >= max_visited:
            cutoff_hit = True
            continue

        solid_n = solid.bit_count()
        ghost_n = ghost.bit_count()

        # Remove solid / remove ghost.
        for i in _iter_bits(solid):
            ns = (solid & ~(1 << i), ghost)
            if ns not in seen:
                seen.add(ns)
                q.append((ns, dist + 1))
        for i in _iter_bits(ghost):
            ns = (solid, ghost & ~(1 << i))
            if ns not in seen:
                seen.add(ns)
                q.append((ns, dist + 1))

        # Convert solid -> ghost.
        if ghost_n < ghost_cap:
            for i in _iter_bits(solid):
                ns = (solid & ~(1 << i), ghost | (1 << i))
                if ns not in seen:
                    seen.add(ns)
                    q.append((ns, dist + 1))

        # Convert ghost -> solid.
        if solid_n < solid_cap:
            for i in _iter_bits(ghost):
                ns = (solid | (1 << i), ghost & ~(1 << i))
                if ns not in seen:
                    seen.add(ns)
                    q.append((ns, dist + 1))

        # Add solid on a node if prerequisites are live (solid or ghost).
        if solid_n < solid_cap:
            for i in range(tree.num_nodes):
                bit = 1 << i
                if live & bit:
                    continue
                pre = tree.prereq_masks[i]
                if (live & pre) == pre:
                    ns = (solid | bit, ghost)
                    if _valid_state(*ns) and ns not in seen:
                        seen.add(ns)
                        q.append((ns, dist + 1))

    return None, len(seen), cutoff_hit


def _bfs_compute_uncompute_relaxed(
    tree: PebbleTree,
    solid_cap: int,
    ghost_cap: int,
    *,
    max_visited: int | None,
) -> tuple[int | None, int, bool]:
    root_bit = 1 << tree.root
    start = (0, 0, 0)  # solid, ghost, seen_root
    goal = (0, 0, 1)
    q = deque([(start, 0)])
    seen = {start}
    cutoff_hit = False

    while q:
        (solid, ghost, seen_root), dist = q.popleft()
        live = solid | ghost
        if (solid, ghost, seen_root) == goal:
            return dist, len(seen), cutoff_hit

        if max_visited is not None and len(seen) >= max_visited:
            cutoff_hit = True
            continue

        solid_n = solid.bit_count()
        ghost_n = ghost.bit_count()

        # Remove solid / ghost.
        for i in _iter_bits(solid):
            ns = (solid & ~(1 << i), ghost, seen_root)
            if ns not in seen:
                seen.add(ns)
                q.append((ns, dist + 1))
        for i in _iter_bits(ghost):
            ns = (solid, ghost & ~(1 << i), seen_root)
            if ns not in seen:
                seen.add(ns)
                q.append((ns, dist + 1))

        # Convert solid -> ghost.
        if ghost_n < ghost_cap:
            for i in _iter_bits(solid):
                ns = (solid & ~(1 << i), ghost | (1 << i), seen_root)
                if ns not in seen:
                    seen.add(ns)
                    q.append((ns, dist + 1))

        # Convert ghost -> solid.
        if solid_n < solid_cap:
            for i in _iter_bits(ghost):
                ns = (solid | (1 << i), ghost & ~(1 << i), seen_root)
                if ns not in seen:
                    seen.add(ns)
                    q.append((ns, dist + 1))

        # Add solid.
        if solid_n < solid_cap:
            for i in range(tree.num_nodes):
                bit = 1 << i
                if live & bit:
                    continue
                pre = tree.prereq_masks[i]
                if (live & pre) == pre:
                    ns_seen = 1 if (seen_root or (bit == root_bit)) else 0
                    ns = (solid | bit, ghost, ns_seen)
                    if ns not in seen:
                        seen.add(ns)
                        q.append((ns, dist + 1))

    return None, len(seen), cutoff_hit


def search_relaxed_ghost_model(
    tree: PebbleTree,
    *,
    solid_cap: int,
    ghost_cap: int,
    max_visited_compute: int | None = None,
    max_visited_full: int | None = None,
) -> GhostSearchResult:
    if solid_cap < 1:
        raise ValueError("solid_cap must be >= 1")
    if ghost_cap < 0:
        raise ValueError("ghost_cap must be >= 0")

    s1, v1, c1 = _bfs_compute_root_relaxed(
        tree, solid_cap, ghost_cap, max_visited=max_visited_compute
    )
    s2, v2, c2 = _bfs_compute_uncompute_relaxed(
        tree, solid_cap, ghost_cap, max_visited=max_visited_full
    )
    return GhostSearchResult(
        possible=(s1 is not None),
        min_steps_compute_root=s1,
        min_steps_compute_uncompute=s2,
        visited_compute=v1,
        visited_full=v2,
        cutoff_hit_compute=c1,
        cutoff_hit_full=c2,
    )


if __name__ == "__main__":
    t = build_balanced_binary_tree(19)
    print(
        f"Relaxed ghost search, m={t.num_leaves}, nodes={t.num_nodes}, height={t.height()}"
    )
    for g in (0, 1, 2, 3, 4):
        r = search_relaxed_ghost_model(
            t,
            solid_cap=5,
            ghost_cap=g,
            max_visited_compute=3_000_000,
            max_visited_full=2_000_000,
        )
        print(
            f"  k=5,g={g}: possible={r.possible}, root={r.min_steps_compute_root}, "
            f"full={r.min_steps_compute_uncompute}, cutoff={r.cutoff_hit_compute}/{r.cutoff_hit_full}, "
            f"visited={r.visited_compute}/{r.visited_full}"
        )
