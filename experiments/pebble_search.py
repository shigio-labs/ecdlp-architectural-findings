"""State-space pebbling search for balanced binary trees.

This is a structural analysis tool for Sprint 2:
- build a balanced binary tree with `m` leaves,
- run shortest-path search in black-pebble state space under a pebble cap,
- estimate step overhead for compute-only and compute+uncompute workflows.

Notes:
- This is a classical black-pebble model, not the full spooky-ghost model of
  CFS. Use outputs as structural bounds/sanity checks, not as direct Toffoli
  counts.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PebbleTree:
    num_nodes: int
    num_leaves: int
    root: int
    prereq_masks: tuple[int, ...]

    def height(self) -> int:
        # Height in edges from leaves to root for the balanced construction.
        if self.num_leaves <= 1:
            return 0
        levels = 0
        n = self.num_leaves
        while n > 1:
            n = (n + 1) // 2
            levels += 1
        return levels


def build_balanced_binary_tree(num_leaves: int) -> PebbleTree:
    if num_leaves < 1:
        raise ValueError("num_leaves must be >= 1")

    # Leaves are nodes [0, num_leaves-1], prereq=0.
    prereq_masks: list[int] = [0] * num_leaves
    current_level = list(range(num_leaves))
    next_node_id = num_leaves

    while len(current_level) > 1:
        nxt: list[int] = []
        i = 0
        while i + 1 < len(current_level):
            left = current_level[i]
            right = current_level[i + 1]
            prereq_masks.append((1 << left) | (1 << right))
            nxt.append(next_node_id)
            next_node_id += 1
            i += 2
        if i < len(current_level):
            # Odd tail promoted to next level unchanged.
            nxt.append(current_level[i])
        current_level = nxt

    root = current_level[0]
    return PebbleTree(
        num_nodes=next_node_id,
        num_leaves=num_leaves,
        root=root,
        prereq_masks=tuple(prereq_masks),
    )


@dataclass(frozen=True)
class PebbleSearchResult:
    possible: bool
    min_steps_compute_root: int | None
    min_steps_compute_uncompute: int | None
    visited_states_compute: int
    visited_states_full: int


def _iter_set_bits(mask: int) -> Iterable[int]:
    while mask:
        lsb = mask & -mask
        yield lsb.bit_length() - 1
        mask ^= lsb


def _bfs_compute_root(tree: PebbleTree, pebble_cap: int) -> tuple[int | None, int]:
    start = 0
    goal_mask = 1 << tree.root
    q = deque([(start, 0)])
    seen = {start}

    while q:
        state, dist = q.popleft()
        if state & goal_mask:
            return dist, len(seen)

        pop = state.bit_count()

        # Remove moves.
        for i in _iter_set_bits(state):
            ns = state & ~(1 << i)
            if ns not in seen:
                seen.add(ns)
                q.append((ns, dist + 1))

        # Add moves.
        if pop < pebble_cap:
            for i in range(tree.num_nodes):
                bit = 1 << i
                if state & bit:
                    continue
                pre = tree.prereq_masks[i]
                if (state & pre) == pre:
                    ns = state | bit
                    if ns not in seen:
                        seen.add(ns)
                        q.append((ns, dist + 1))

    return None, len(seen)


def _bfs_compute_uncompute(tree: PebbleTree, pebble_cap: int) -> tuple[int | None, int]:
    # State augmented with "seen_root" flag:
    # key = (state_bitmask, seen_root_bool)
    start = (0, 0)
    goal = (0, 1)
    root_bit = 1 << tree.root

    q = deque([(start, 0)])
    seen = {start}

    while q:
        (state, seen_root), dist = q.popleft()
        if (state, seen_root) == goal:
            return dist, len(seen)

        pop = state.bit_count()

        # Remove moves.
        for i in _iter_set_bits(state):
            ns = state & ~(1 << i)
            key = (ns, seen_root)
            if key not in seen:
                seen.add(key)
                q.append((key, dist + 1))

        # Add moves.
        if pop < pebble_cap:
            for i in range(tree.num_nodes):
                bit = 1 << i
                if state & bit:
                    continue
                pre = tree.prereq_masks[i]
                if (state & pre) == pre:
                    ns = state | bit
                    ns_seen_root = 1 if (seen_root or (ns & root_bit)) else 0
                    key = (ns, ns_seen_root)
                    if key not in seen:
                        seen.add(key)
                        q.append((key, dist + 1))

    return None, len(seen)


def search_tree(tree: PebbleTree, pebble_cap: int) -> PebbleSearchResult:
    if pebble_cap < 1:
        raise ValueError("pebble_cap must be >= 1")

    s1, v1 = _bfs_compute_root(tree, pebble_cap)
    s2, v2 = _bfs_compute_uncompute(tree, pebble_cap)
    return PebbleSearchResult(
        possible=(s1 is not None),
        min_steps_compute_root=s1,
        min_steps_compute_uncompute=s2,
        visited_states_compute=v1,
        visited_states_full=v2,
    )


def search_compute_root_only(tree: PebbleTree, pebble_cap: int) -> tuple[int | None, int]:
    """Fast path when we only need root-pebbling distance and visited states."""
    if pebble_cap < 1:
        raise ValueError("pebble_cap must be >= 1")
    return _bfs_compute_root(tree, pebble_cap)


if __name__ == "__main__":
    tree = build_balanced_binary_tree(19)
    print(
        f"Tree m={tree.num_leaves}, nodes={tree.num_nodes}, height={tree.height()}, root={tree.root}"
    )
    for k in (4, 5, 6, 7):
        s1, v1 = search_compute_root_only(tree, k)
        print(
            f"  k={k}: compute_root={s1}, visited_compute={v1}"
        )
    for k in (6, 7):
        r = search_tree(tree, k)
        print(
            f"  k={k} full: possible={r.possible}, "
            f"compute_uncompute={r.min_steps_compute_uncompute}, "
            f"visited_full={r.visited_states_full}"
        )
