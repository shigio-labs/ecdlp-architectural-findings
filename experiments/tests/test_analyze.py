"""Tests for the analyze.py aggregation pipeline.

Smoke-level: handles empty data, missing certificates, table-printing edge cases.
"""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from experiments import analyze


def test_load_jsonl_missing(tmp_path):
    assert analyze.load_jsonl(tmp_path / "does_not_exist.jsonl") == []


def test_load_jsonl_empty(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    assert analyze.load_jsonl(p) == []


def test_load_jsonl_with_blank_lines(tmp_path):
    p = tmp_path / "blanks.jsonl"
    p.write_text('{"a": 1}\n\n   \n{"b": 2}\n')
    rs = analyze.load_jsonl(p)
    assert rs == [{"a": 1}, {"b": 2}]


def test_assert_certificates_clean_passes_on_clean(capsys):
    records = [{"certified_when_wrong": 0}, {"certified_when_wrong": 0}]
    analyze.assert_certificates_clean(records, "test")
    out = capsys.readouterr().out
    assert "all certificates honest" in out


def test_assert_certificates_clean_exits_on_dirty(capsys):
    records = [{"certified_when_wrong": 0}, {"certified_when_wrong": 1}]
    with pytest.raises(SystemExit):
        analyze.assert_certificates_clean(records, "test")
    err = capsys.readouterr().err
    assert "CERTIFICATE BUG" in err


def test_fmt_rate_zero():
    assert analyze.fmt_rate(0) == "0       "


def test_fmt_rate_none():
    assert "--" in analyze.fmt_rate(None)


def test_fmt_rate_nan():
    import math
    assert "--" in analyze.fmt_rate(float("nan"))


def test_fmt_rate_percent():
    assert "%" in analyze.fmt_rate(0.05)


def test_fmt_rate_ppm():
    assert "ppm" in analyze.fmt_rate(1e-5)
