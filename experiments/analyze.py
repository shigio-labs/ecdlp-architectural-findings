"""Aggregate jsonl outputs from experiments and produce summary tables.

Usage:
    .venv/Scripts/python.exe -m experiments.analyze
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).parent


def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def assert_certificates_clean(records: list[dict], name: str) -> None:
    bad = [r for r in records if r.get("certified_when_wrong", 0) > 0]
    if bad:
        print(f"!!! {len(bad)} {name} records with certified_when_wrong > 0 — CERTIFICATE BUG", file=sys.stderr)
        for b in bad[:3]:
            print(f"   {b}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"  {name}: {len(records)} records, all certificates honest")


def fmt_rate(rate) -> str:
    import math
    if rate is None or (isinstance(rate, float) and math.isnan(rate)):
        return "   --   "
    if rate == 0:
        return "0       "
    if rate >= 1e-3:
        return f"{rate*100:>6.3f}%"
    return f"{rate*1e6:>5.1f}ppm"


def print_table_uniform(records: list[dict]) -> None:
    """abort_rate vs (k_c, r) for each (family, use_offset)."""
    by = defaultdict(dict)
    for r in records:
        key = (r["family"], r["use_offset"])
        by[key][(r["k_c"], r["precision_bits"])] = r["abort_rate"]

    for family, use_offset in sorted(by):
        print()
        print(f"=== {family}  use_offset={use_offset} ===")
        # rows: k_c, columns: r
        k_cs = sorted({k_c for k_c, _ in by[(family, use_offset)]})
        rs = sorted({r for _, r in by[(family, use_offset)]})
        header = "  k_c \\ r  | " + " | ".join(f"{r:>8}" for r in rs)
        print(header)
        print(" " + "-" * (len(header) - 1))
        for k_c in k_cs:
            row_vals = [
                fmt_rate(by[(family, use_offset)].get((k_c, r)))
                for r in rs
            ]
            print(f"   k_c={k_c:>2}  | " + " | ".join(f"{v:>8}" for v in row_vals))


def print_table_postmul(records: list[dict]) -> None:
    """abort_rate vs (k_c, r) for each (family, distribution, use_offset)."""
    by = defaultdict(dict)
    for r in records:
        key = (r["family"], r["distribution"], r["use_offset"])
        by[key][(r["k_c"], r["precision_bits"])] = r["abort_rate"]

    for family, dist, use_offset in sorted(by):
        print()
        print(f"=== {family} {dist} use_offset={use_offset} ===")
        k_cs = sorted({k_c for k_c, _ in by[(family, dist, use_offset)]})
        rs = sorted({r for _, r in by[(family, dist, use_offset)]})
        header = "  k_c \\ r  | " + " | ".join(f"{r:>8}" for r in rs)
        print(header)
        print(" " + "-" * (len(header) - 1))
        for k_c in k_cs:
            row_vals = [
                fmt_rate(by[(family, dist, use_offset)].get((k_c, r)))
                for r in rs
            ]
            print(f"   k_c={k_c:>2}  | " + " | ".join(f"{v:>8}" for v in row_vals))


def print_table_adversarial(records: list[dict]) -> None:
    """For each (family, k_c, target_frac), show abort rate at each (r, offset)."""
    by = defaultdict(dict)
    for rec in records:
        key = (rec["family"], rec["k_c"], rec["target_frac"], rec["use_offset"])
        by[key][rec["precision_bits"]] = rec["abort_rate"]

    for family, k_c, tf, use_offset in sorted(by):
        rs = sorted(by[(family, k_c, tf, use_offset)])
        rates = [fmt_rate(by[(family, k_c, tf, use_offset)][r]) for r in rs]
        print(
            f"  {family:>10} k_c={k_c:>2} target={tf:.0e} offset={int(use_offset)}: "
            + "  ".join(f"r={r}={v}" for r, v in zip(rs, rates))
        )


def compare_uniform_vs_postmul(uniform: list[dict], postmul: list[dict]) -> None:
    """For matching (family, k_c, r, use_offset), print uniform vs post-mul rates."""
    u_by = {
        (r["family"], r["k_c"], r["precision_bits"], r["use_offset"]): r["abort_rate"]
        for r in uniform
    }
    p_by = defaultdict(dict)
    for r in postmul:
        key = (r["family"], r["k_c"], r["precision_bits"], r["use_offset"])
        p_by[key][r["distribution"]] = r["abort_rate"]

    print()
    print("=== Uniform vs post-multiplication abort rates (interesting cells) ===")
    print(
        f"{'family':>10} {'k_c':>4} {'r':>3} {'off':>4} | "
        f"{'uniform':>10} | {'modMc':>10} | {'modp':>10} | ratio_modMc"
    )
    for key in sorted(u_by):
        family, k_c, r, off = key
        u = u_by[key]
        p_modMc = p_by[key].get("product_modMc")
        p_modp = p_by[key].get("product_modp")
        ratio = (p_modMc / u) if (u and p_modMc) else None
        ratio_str = f"{ratio:>5.2f}x" if ratio is not None else "    -"
        print(
            f"{family:>10} {k_c:>4} {r:>3} {int(off):>4} | "
            f"{fmt_rate(u):>10} | "
            f"{fmt_rate(p_modMc) if p_modMc is not None else '-':>10} | "
            f"{fmt_rate(p_modp) if p_modp is not None else '-':>10} | "
            f"{ratio_str:>5}"
        )


def print_table_montgomery(records: list[dict]) -> None:
    """Same shape as exp1 (Montgomery == uniform-like check)."""
    by = defaultdict(dict)
    for r in records:
        key = (r["family"], r["use_offset"])
        by[key][(r["k_c"], r["precision_bits"])] = r["abort_rate"]

    for family, use_offset in sorted(by):
        print()
        print(f"=== {family}  use_offset={use_offset}  (Montgomery t) ===")
        k_cs = sorted({k_c for k_c, _ in by[(family, use_offset)]})
        rs = sorted({r for _, r in by[(family, use_offset)]})
        header = "  k_c \\ r  | " + " | ".join(f"{r:>8}" for r in rs)
        print(header)
        print(" " + "-" * (len(header) - 1))
        for k_c in k_cs:
            row_vals = [
                fmt_rate(by[(family, use_offset)].get((k_c, r)))
                for r in rs
            ]
            print(f"   k_c={k_c:>2}  | " + " | ".join(f"{v:>8}" for v in row_vals))


def main() -> None:
    print("=== Loading data ===")
    uniform = load_jsonl(HERE / "exp1_uniform" / "data.jsonl")
    postmul = load_jsonl(HERE / "exp2_postmul" / "data.jsonl")
    montgomery = load_jsonl(HERE / "exp2b_montgomery" / "data.jsonl")
    adv = load_jsonl(HERE / "exp3_adversarial" / "data.jsonl")
    chain = load_jsonl(HERE / "exp4_shor_chain" / "data.jsonl")
    print(f"  uniform records:      {len(uniform)}")
    print(f"  post-mul records:     {len(postmul)}")
    print(f"  montgomery records:   {len(montgomery)}")
    print(f"  adversarial records:  {len(adv)}")
    print(f"  shor-chain records:   {len(chain)}")
    print()

    if uniform:
        assert_certificates_clean(uniform, "exp1_uniform")
    if postmul:
        assert_certificates_clean(postmul, "exp2_postmul")
    if montgomery:
        assert_certificates_clean(montgomery, "exp2b_montgomery")
    if adv:
        assert_certificates_clean(adv, "exp3_adversarial")

    if uniform:
        print()
        print("=" * 70)
        print("EXP 1: UNIFORM ABORT RATES")
        print_table_uniform(uniform)
    if postmul:
        print()
        print("=" * 70)
        print("EXP 2: POST-MULTIPLICATION ABORT RATES")
        print_table_postmul(postmul)
        if uniform:
            compare_uniform_vs_postmul(uniform, postmul)
    if montgomery:
        print()
        print("=" * 70)
        print("EXP 2b: MONTGOMERY-STYLE INTERMEDIATE ABORT RATES")
        print_table_montgomery(montgomery)
    if adv:
        print()
        print("=" * 70)
        print("EXP 3: ADVERSARIAL POOLS (abort rate at each r)")
        print_table_adversarial(adv)
    if chain:
        print()
        print("=" * 70)
        print("EXP 4: SHOR CHAIN SURVIVAL")
        for c in chain:
            print(
                f"  {c['family']:>10} k_c={c['k_c']:>2} r={c['precision_bits']:>2} "
                f"offset={int(c['use_offset'])}: "
                f"survived={c['survived']}/{c['n_chains']} = {c['survival_rate']:.4f}, "
                f"implied per-step p={c['implied_per_step_abort']:.6f}"
            )


if __name__ == "__main__":
    main()
