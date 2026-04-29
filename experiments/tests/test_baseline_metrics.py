"""Regression checks for published baseline claims.

These tests lock the current measured baseline so future optimization work
can be evaluated against stable numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

from experiments import analyze


HERE = Path(__file__).resolve().parents[1]


def _find_record(records: list[dict], **match) -> dict:
    for rec in records:
        if all(rec.get(k) == v for k, v in match.items()):
            return rec
    raise AssertionError(f"record not found: {match}")


def test_exp1_baseline_recommended_cell():
    records = analyze.load_jsonl(HERE / "exp1_uniform" / "data.jsonl")
    assert len(records) == 144
    assert all(r.get("certified_when_wrong", 0) == 0 for r in records)

    rec = _find_record(
        records,
        family="wide20",
        k_c=13,
        precision_bits=14,
        use_offset=True,
    )
    # Published recommended point: ~50 ppm.
    assert rec["abort_rate"] == 5.0e-05


def test_exp2b_montgomery_matches_uniform_scale():
    records = analyze.load_jsonl(HERE / "exp2b_montgomery" / "data.jsonl")
    assert len(records) == 144
    assert all(r.get("certified_when_wrong", 0) == 0 for r in records)

    rec = _find_record(
        records,
        family="wide20",
        k_c=13,
        precision_bits=14,
        use_offset=True,
    )
    # Same order of magnitude as exp1 recommendation.
    assert 3.0e-05 <= rec["abort_rate"] <= 8.0e-05


def test_exp4_chain_survival_recommended_cell():
    records = analyze.load_jsonl(HERE / "exp4_shor_chain" / "data.jsonl")
    assert len(records) == 9

    rec = _find_record(
        records,
        family="wide20",
        k_c=13,
        precision_bits=14,
        use_offset=True,
    )
    assert rec["n_chains"] == 2000
    assert rec["chain_length"] == 512
    assert rec["survived"] == 1951
    assert rec["survival_rate"] == 0.9755
    assert 4.0e-05 <= rec["implied_per_step_abort"] <= 6.0e-05


def test_exp5_cluster_independence_signal_is_healthy():
    rec = json.loads((HERE / "exp5_cluster" / "data.json").read_text(encoding="utf-8"))
    assert rec["family"] == "wide20"
    assert rec["k_c"] == 13
    assert rec["precision_bits"] == 14
    assert rec["use_offset"] is True
    assert abs(rec["lag1_autocorrelation_frac_S"]) < 0.01
    assert rec["false_chi2_vs_poisson"] < 1.0


def test_exp6_threshold_has_expected_cliff_behavior():
    records = analyze.load_jsonl(HERE / "exp6_threshold" / "data.jsonl")
    assert len(records) > 0
    assert all(r.get("certified_when_wrong", 0) == 0 for r in records)

    # Near T ~= 0 and r=14 no-offset, abort should be well below 1%.
    low_t = [
        r
        for r in records
        if abs(r["T_log2_Mc_over_p"]) < 0.1
        and r["precision_bits"] == 14
        and r["use_offset"] is False
    ]
    assert low_t, "missing low-T sample"
    assert min(r["abort_rate"] for r in low_t) < 0.01

    # In the high-T region and r=14 no-offset, abort should hit the cliff.
    high_t = [
        r
        for r in records
        if r["T_log2_Mc_over_p"] > 11.0
        and r["precision_bits"] == 14
        and r["use_offset"] is False
    ]
    assert high_t, "missing high-T sample"
    assert max(r["abort_rate"] for r in high_t) > 0.99
