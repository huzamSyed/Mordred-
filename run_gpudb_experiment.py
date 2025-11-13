#!/usr/bin/env python3
import argparse
import csv
import re
import sys
from pathlib import Path

try:
    import pexpect
except ImportError:
    print("Please install pexpect:  pip install pexpect", file=sys.stderr)
    sys.exit(1)

import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt

# -------- Robust prompt matchers (ANSI/typos/no-newline tolerant) --------
ANSI = r"(?:\x1B\[[0-9;?]*[ -/]*[@-~])*"  # ANSI escapes (optional, zero or more)
MENU_PROMPT_RE = re.compile(ANSI + r"Your Input:\s*$", re.MULTILINE)
COLUMN_PROMPT_RE = re.compile(ANSI + r"Column to cache:\s*$", re.IGNORECASE | re.MULTILINE)
SEGMENT_PROMPT_RE = re.compile(
    ANSI + r"enter\s+the\s+number\s+of\s+segments\s+to\s+be\s+c[a|e]h?c?ed\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE
)

# -------- Markers to split fused vs non-fused blocks --------
# We split each response into two blocks by the "Query: 10 ..." headers.
QUERY_HEADER_RE = re.compile(r"\n?\s*Query:\s*10\b[^\n]*", re.IGNORECASE)

# -------- Metric regexes (strict to 'Kernel time GPU') --------
RE_FUSED_FILTER_PROBE = re.compile(r"Filter\s+Probe\s+Kernel\s+time\s+GPU:\s*([0-9]*\.?[0-9]+)")
RE_NONFUSED_FILTER    = re.compile(r"Filter\s+Kernel\s+time\s+GPU:\s*([0-9]*\.?[0-9]+)")
RE_NONFUSED_PROBE     = re.compile(r"Probe\s+Kernel\s+time\s+GPU:\s*([0-9]*\.?[0-9]+)")
RE_QUERY_EXEC_TIME    = re.compile(r"Query\s+Execution\s+Time:\s*([0-9]*\.?[0-9]+)")

def wait_for_menu(child, timeout):
    child.expect(MENU_PROMPT_RE, timeout=timeout)
    return child.before + child.after

def drive_initial_cache(child, segments, timeout):
    # Wait for the first menu
    wait_for_menu(child, timeout)

    # Send 'cache'
    child.sendline("cache")
    # Either column prompt or menu (if caching not needed)
    i = child.expect([COLUMN_PROMPT_RE, MENU_PROMPT_RE], timeout=timeout)
    if i == 1:
        return  # back to menu already; skip

    # Column name: x
    child.sendline("x")

    # Segment prompt can be flaky; try to catch it but proceed anyway
    try:
        child.expect([SEGMENT_PROMPT_RE, MENU_PROMPT_RE], timeout=10)
    except pexpect.TIMEOUT:
        pass

    # Send number of segments regardless
    child.sendline(str(segments))

    # Back to menu (may print “Cumulated Time…” etc. first)
    wait_for_menu(child, timeout)

def run_query_block(child, lo_price, timeout):
    """
    Sends:
      1  -> Run Specific Query
      10 -> Query ID
      lo_price -> lower bound for lo_extended_price
    Reads until the menu returns (after fused + non-fused).
    """
    child.sendline("1")
    child.expect(re.compile(r"Input\s+Query:\s*$", re.IGNORECASE | re.MULTILINE), timeout=timeout)
    child.sendline("10")
    child.sendline(str(lo_price))
    child.expect(MENU_PROMPT_RE, timeout=timeout)
    return child.before + child.after

def split_runs(block):
    """
    Split the output block into two sub-blocks corresponding to:
      [0] fused run
      [1] non-fused run
    Uses 'Query: 10 ...' headers as anchors.
    """
    headers = list(QUERY_HEADER_RE.finditer(block))
    if len(headers) < 2:
        # Not enough structure; return the whole block as fused, empty as non-fused
        return [block, ""]
    # Slice: from header0 to header1, and header1 to end
    h0 = headers[0].start()
    h1 = headers[1].start()
    fused_block = block[h0:h1]
    nonfused_block = block[h1:]
    return [fused_block, nonfused_block]

def parse_metrics(block):
    """
    Extract exactly the requested metrics from the correct run:
      Fused:
        - Filter Probe Kernel time GPU -> fused_filter_probe_kernel_time_gpu
        - Query Execution Time         -> fused_query_execution_time
      Non-fused:
        - Filter Kernel time GPU       -> nonfused_filter_kernel_time_gpu
        - Probe  Kernel time GPU       -> nonfused_probe_kernel_time_gpu
        - Query Execution Time         -> nonfused_query_execution_time
    """
    fused_block, nonfused_block = split_runs(block)

    # Fused metrics (from fused block only)
    fused_filter_probe = RE_FUSED_FILTER_PROBE.search(fused_block)
    fused_exec         = RE_QUERY_EXEC_TIME.search(fused_block)

    # Non-fused metrics (from non-fused block only)
    nonfused_filter = RE_NONFUSED_FILTER.search(nonfused_block)
    nonfused_probe  = RE_NONFUSED_PROBE.search(nonfused_block)
    nonfused_exec   = RE_QUERY_EXEC_TIME.search(nonfused_block)

    return {
        "fused_filter_probe_kernel_time_gpu": float(fused_filter_probe.group(1)) if fused_filter_probe else None,
        "fused_query_execution_time": float(fused_exec.group(1)) if fused_exec else None,
        "nonfused_filter_kernel_time_gpu": float(nonfused_filter.group(1)) if nonfused_filter else None,
        "nonfused_probe_kernel_time_gpu": float(nonfused_probe.group(1)) if nonfused_probe else None,
        "nonfused_query_execution_time": float(nonfused_exec.group(1)) if nonfused_exec else None,
        "raw_block": block,
    }

def plot_five_series(out_png, rows):
    xs      = [r["lo_extended_price"] for r in rows]
    fusedFP = [r["fused_filter_probe_kernel_time_gpu"] for r in rows]
    fusedQ  = [r["fused_query_execution_time"] for r in rows]
    nfFilt  = [r["nonfused_filter_kernel_time_gpu"] for r in rows]
    nfProbe = [r["nonfused_probe_kernel_time_gpu"] for r in rows]
    nfQ     = [r["nonfused_query_execution_time"] for r in rows]

    plt.figure(figsize=(11, 6))
    plt.plot(xs, fusedFP, label="Fused: Filter-Probe GPU Time")
    plt.plot(xs, fusedQ,  label="Fused: Query Execution Time")
    plt.plot(xs, nfFilt,  label="Non-fused: Filter GPU Time")
    plt.plot(xs, nfProbe, label="Non-fused: Probe GPU Time")
    plt.plot(xs, nfQ,     label="Non-fused: Query Execution Time")
    plt.xlabel("lo_extended_price (lower bound; higher → more selective)")
    plt.ylabel("Time (ms)")
    plt.title("Query 10 — Fused vs Non-fused timings vs lo_extended_price")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)

def main():
    ap = argparse.ArgumentParser(description="Run GPUDB Query 10, extract fused/non-fused metrics, write CSV, plot 5 series.")
    ap.add_argument("--bin", default="./bin/gpudb/main")
    ap.add_argument("--segments", type=int, default=4)
    ap.add_argument("--start", type=int, default=100000)
    ap.add_argument("--end", type=int, default=10500000)
    ap.add_argument("--step", type=int, default=100000)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--csv", default="gpudb_q10_timings.csv")
    ap.add_argument("--png", default="gpudb_q10_plot.png")
    ap.add_argument("--logdir", default="gpudb_logs")
    ap.add_argument("--skip-cache", action="store_true", help="Skip the cache setup if already done.")
    args = ap.parse_args()

    Path(args.logdir).mkdir(parents=True, exist_ok=True)

    child = pexpect.spawn(args.bin, encoding="utf-8", timeout=args.timeout)
    child.logfile = sys.stdout  # echo for transparency

    if not args.skip_cache:
        drive_initial_cache(child, args.segments, args.timeout)
    else:
        wait_for_menu(child, args.timeout)

    rows = []
    for i, lo in enumerate(range(args.start, args.end + 1, args.step), 1):
        block = run_query_block(child, lo, args.timeout)
        m = parse_metrics(block)

        # keep raw for audit/debug
        with open(Path(args.logdir) / f"block_{i}_{lo}.log", "w", encoding="utf-8") as f:
            f.write(block)

        rows.append({
            "lo_extended_price": lo,
            "fused_filter_probe_kernel_time_gpu": m["fused_filter_probe_kernel_time_gpu"],
            "fused_query_execution_time": m["fused_query_execution_time"],
            "nonfused_filter_kernel_time_gpu": m["nonfused_filter_kernel_time_gpu"],
            "nonfused_probe_kernel_time_gpu": m["nonfused_probe_kernel_time_gpu"],
            "nonfused_query_execution_time": m["nonfused_query_execution_time"],
        })

    # Try to exit
    child.sendline("6")
    try:
        child.expect(pexpect.EOF, timeout=10)
    except pexpect.TIMEOUT:
        pass

    # CSV
    headers = [
        "lo_extended_price",
        "fused_filter_probe_kernel_time_gpu",
        "fused_query_execution_time",
        "nonfused_filter_kernel_time_gpu",
        "nonfused_probe_kernel_time_gpu",
        "nonfused_query_execution_time",
    ]
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)

    # Plot the five requested series
    plot_five_series(args.png, rows)

    print(f"\n✅ Done")
    print(f"CSV:  {args.csv}")
    print(f"Plot: {args.png}")
    print(f"Logs: {args.logdir}/")

if __name__ == "__main__":
    main()
