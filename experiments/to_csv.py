"""Convert experiment jsonl outputs to CSV for spreadsheet inspection."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


HERE = Path(__file__).parent


def jsonl_to_csv(in_path: Path, out_path: Path, fields: list[str]) -> None:
    if not in_path.exists():
        print(f"missing: {in_path}", file=sys.stderr)
        return
    rows = [json.loads(l) for l in in_path.read_text().splitlines() if l.strip()]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            # Flatten diff_distribution into one column
            if "diff_distribution" in r:
                r = dict(r)
                r["diff_distribution"] = json.dumps(r["diff_distribution"])
            w.writerow(r)
    print(f"wrote {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    jsonl_to_csv(
        HERE / "exp1_uniform" / "data.jsonl",
        HERE / "exp1_uniform" / "data.csv",
        [
            "family", "k_c", "log2_M_c", "log2_M_c_minus_log2_p",
            "precision_bits", "use_offset", "n_samples", "seed",
            "aborts", "abort_rate",
            "certified_correct", "certified_when_wrong",
            "diff_distribution", "elapsed_seconds",
        ],
    )
    jsonl_to_csv(
        HERE / "exp2_postmul" / "data.jsonl",
        HERE / "exp2_postmul" / "data.csv",
        [
            "family", "k_c", "log2_M_c", "log2_M_c_minus_log2_p",
            "distribution", "precision_bits", "use_offset",
            "n_samples", "seed",
            "aborts", "abort_rate",
            "certified_correct", "certified_when_wrong",
            "diff_distribution", "elapsed_seconds",
        ],
    )
    jsonl_to_csv(
        HERE / "exp2b_montgomery" / "data.jsonl",
        HERE / "exp2b_montgomery" / "data.csv",
        [
            "family", "k_c", "log2_M_c", "log2_M_c_minus_log2_p",
            "precision_bits", "use_offset", "n_samples", "seed",
            "aborts", "abort_rate",
            "certified_correct", "certified_when_wrong",
            "diff_distribution", "elapsed_seconds",
        ],
    )
    jsonl_to_csv(
        HERE / "exp3_adversarial" / "data.jsonl",
        HERE / "exp3_adversarial" / "data.csv",
        [
            "family", "k_c", "log2_M_c", "log2_M_c_minus_log2_p",
            "target_frac", "pool_size", "rejection_attempts", "rejection_rate",
            "precision_bits", "use_offset", "seed",
            "aborts", "abort_rate",
            "certified_correct", "certified_when_wrong",
            "diff_distribution",
        ],
    )
    jsonl_to_csv(
        HERE / "exp4_shor_chain" / "data.jsonl",
        HERE / "exp4_shor_chain" / "data.csv",
        [
            "family", "k_c", "log2_M_c", "log2_M_c_minus_log2_p",
            "precision_bits", "use_offset",
            "chain_length", "n_chains", "seed",
            "survived", "survival_rate",
            "implied_per_step_abort", "median_abort_step",
            "elapsed_seconds",
        ],
    )
