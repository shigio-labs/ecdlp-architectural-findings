"""Force UTF-8 stdout/stderr on Windows where the default codepage (cp1251 on
Russian-locale Windows) cannot encode unicode math symbols like ×, ≈, →.

Import this from any entry-point script:
    from delta._encoding import _  # one-time setup side-effect
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

_ = None  # importable sentinel
