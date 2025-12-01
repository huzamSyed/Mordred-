import os
import re
import csv
from collections import defaultdict
import matplotlib.pyplot as plt  # NEW
import numpy as np               # NEW

LOG_PATH = "sf40_0GB"

METRIC_NAMES = [
    "Query Prepare Time",
    "Query Prepare Time using cpu",
    "Query Optimization Time",
    "Query Execution Time",
    "CPU Time",
    "GPU Time",
    "Transfer Time",
    "Malloc Time",
    "Build time",
    "Probe time",
    "Merge time",

    "Filter Build Kernel time CPU",
    "Filter Kernel time CPU",
    "Filter Probe Kernel time CPU",
    "Filter Probe Aggr Kernel time CPU",

    "Filter Build Kernel time GPU",
    "Filter Kernel time GPU",
    "Filter Probe Kernel time GPU",
    "Filter Probe Aggr Kernel time GPU",

    "Probe Group Kernel time CPU",
    "Probe Group Kernel time GPU",
    "Group Kernel time CPU",
    "Group Kernel time GPU",
    "Aggr Kernel time CPU",
    "Aggr Kernel time GPU",

    "Build Kernel time GPU",
    "Build Kernel time CPU",
    "Probe Kernel time GPU",
]

# More tolerant metric regexes: optional colon, arbitrary whitespace
METRIC_REGEXES = {
    name: re.compile(
        rf"{re.escape(name)}\s*:?\s*([-+]?[0-9]*\.?[0-9]+)"
    )
    for name in METRIC_NAMES
}

# Scan metrics in order of decreasing name length to avoid substring clashes
METRIC_NAMES_SORTED = sorted(METRIC_NAMES, key=len, reverse=True)

# Query header, allow leading spaces
RE_QUERY_HEADER = re.compile(r"^\s*Query:\s*(\d+)")
# Epoch markers
RE_EPOCH_START = re.compile(r"epoch start")
RE_EPOCH_END   = re.compile(r"epoch end")

# Summary fractions
RE_FRACTION = re.compile(
    r"Query\s+(\d+)\s+fraction:\s*([0-9.eE+-]+)\s+total:\s*(\d+)\s+cached:\s*(\d+)"
)

# Preamble for the "real" Run Experiment section
RE_CACHED_SEGMENT = re.compile(r"^Cached segment:\s+999\b.*Cache total:\s+1000")
RE_RUN_EXPERIMENT = re.compile(r"^\s*Run Experiment")
# Experiments begin at this line (note spelling in the log)
RE_RUN_EXPERIEMENT = re.compile(r"^\s*Run Experiement")


def to_int(val_str: str) -> int:
    # ignore decimals
    try:
        return int(float(val_str))
    except ValueError:
        return 0


def parse_log(path: str):
    """
    Parse the log, enforcing:
      - start from the first 'Run Experiment'
      - epochs delimited by 'epoch start' / 'epoch end'
      - (rest of logic unchanged)
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Find starting point: the "Run Experiment" that marks beginning of the runs
    i = 0
    # NOTE: spelling is exactly "Run Experiment" in your log
    while i < len(lines) and "Run Experiment" not in lines[i]:
        i += 1
    if i >= len(lines):
        raise RuntimeError("Can't find 'Run Experiment' in log")
    # Start parsing after this line
    i += 1

    epoch_stats = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: {"sum": 0, "count": 0}))
    )
    epoch_fraction = defaultdict(dict)

    current_epoch = 0
    inside_epoch = False

    # from here down keep your existing epoch/query parsing logic
    while i < len(lines):
        line = lines[i]

        # Look for epoch start
        if not inside_epoch:
            if RE_EPOCH_START.search(line):
                inside_epoch = True
                current_epoch += 1
                i += 1
            else:
                i += 1
            continue

        # Inside an epoch
        # Handle epoch end
        if RE_EPOCH_END.search(line):
            inside_epoch = False
            i += 1
            continue

        # Parse fraction summary lines
        mfrac = RE_FRACTION.search(line)
        if mfrac:
            qid = int(mfrac.group(1))
            frac = float(mfrac.group(2))
            total = int(mfrac.group(3))
            cached = int(mfrac.group(4))
            epoch_fraction[current_epoch][qid] = {
                "fraction": frac,
                "total": total,
                "cached": cached,
            }
            i += 1
            continue

        # Look for a bare query id line that precedes two Query: blocks.
        # The original log typically has:
        #   31
        #
        #    Query: 31 ...
        #    ...
        mbare = re.match(r"^\s*(\d+)\s*$", line)
        if mbare:
            # Look ahead for "Query:" to confirm this is a group
            la = i + 1
            while la < len(lines) and lines[la].strip() == "":
                la += 1
            if la >= len(lines) or not RE_QUERY_HEADER.search(lines[la]):
                i += 1
                continue  # Not a real group marker

            qid_str = mbare.group(1)
            qid = int(qid_str)

            # Collect two executions of this query
            execs = []
            i = la
            while i < len(lines) and len(execs) < 2:
                m_q = RE_QUERY_HEADER.search(lines[i])
                if m_q:
                    # Start parsing one execution
                    exec_metrics = defaultdict(int)
                    i += 1
                    while i < len(lines):
                        l = lines[i].rstrip("\n")

                        # Stop if new "Query:" starts (another execution), or epoch end
                        if RE_QUERY_HEADER.search(l) or RE_EPOCH_END.search(l):
                            break

                        # Collect metrics on this line (sum all occurrences)
                        used_spans = []
                        for mname in METRIC_NAMES_SORTED:
                            rgx = METRIC_REGEXES[mname]
                            for mm in rgx.finditer(l):
                                span = mm.span()
                                # avoid overlapping matches
                                if any(not (span[1] <= s or span[0] >= e) for s, e in used_spans):
                                    continue
                                used_spans.append(span)
                                v = to_int(mm.group(1))
                                exec_metrics[mname] += v

                        # End of this execution: line containing Malloc Time
                        if "Malloc Time" in l:
                            i += 1
                            break

                        i += 1

                    # Save execution
                    execs.append(exec_metrics)
                else:
                    # Skip until next Query or epoch end
                    if RE_EPOCH_END.search(lines[i]):
                        break
                    i += 1

            # Choose execution with smaller Query Execution Time
            if execs:
                best = min(
                    execs,
                    key=lambda m: m.get("Query Execution Time", 10**12),
                )
                # aggregate this instance into epoch_stats
                for mname, val in best.items():
                    st = epoch_stats[current_epoch][qid][mname]
                    st["sum"] += val
                    st["count"] += 1

            continue  # processed this group

        # Normal line inside epoch but not fraction/epoch-end/group
        i += 1

    return epoch_stats, epoch_fraction


def write_epoch_csvs(epoch_stats, epoch_fraction, base_log: str):
    """
    For each epoch, write one CSV with per-query aggregates.
    Columns:
      epoch,query_id,num_instances,<metric>_sum,<metric>_avg,fraction,total,cached
    """
    out_dir = "epoch_csv"
    os.makedirs(out_dir, exist_ok=True)

    for epoch in sorted(epoch_stats.keys()):
        qstats = epoch_stats[epoch]

        # Build columns
        base_cols = ["epoch", "query_id", "num_instances"]
        metric_sum_cols = [m.replace(" ", "_") + "_sum" for m in METRIC_NAMES]
        metric_avg_cols = [m.replace(" ", "_") + "_avg" for m in METRIC_NAMES]
        frac_cols = ["fraction", "total", "cached"]
        cols = base_cols + metric_sum_cols + metric_avg_cols + frac_cols

        out_path = os.path.join(out_dir, f"epoch_{epoch}.csv")
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cols)
            writer.writeheader()

            for qid in sorted(qstats.keys()):
                metrics = qstats[qid]
                num_instances = 0
                # num_instances is count of times Query Execution Time observed
                # but each metric has its own count; use CPU Time as proxy if present
                if "Query Execution Time" in metrics:
                    num_instances = metrics["Query Execution Time"]["count"]
                else:
                    # fallback: max count across metrics
                    num_instances = max((st["count"] for st in metrics.values()), default=0)

                row = {
                    "epoch": epoch,
                    "query_id": qid,
                    "num_instances": num_instances,
                }

                # sums and avgs
                for mname in METRIC_NAMES:
                    st = metrics.get(mname, {"sum": 0, "count": 0})
                    s = st["sum"]
                    c = st["count"] if st["count"] > 0 else num_instances
                    key_sum = mname.replace(" ", "_") + "_sum"
                    key_avg = mname.replace(" ", "_") + "_avg"
                    row[key_sum] = s
                    row[key_avg] = (s / c) if c > 0 else 0.0

                # add fraction/total/cached if present
                frac = epoch_fraction.get(epoch, {}).get(qid, None)
                if frac:
                    row["fraction"] = frac["fraction"]
                    row["total"] = frac["total"]
                    row["cached"] = frac["cached"]
                else:
                    row["fraction"] = ""
                    row["total"] = ""
                    row["cached"] = ""

                writer.writerow(row)

        print(f"Wrote {out_path}")


def plot_epoch_metrics(epoch_stats, out_dir="epoch_plots"):
    """
    For each epoch, generate a bar chart of:
      Probe time, Transfer Time, GPU Time, CPU Time, Query Execution Time
    per query (using the *avg* values).
    One PNG per epoch: epoch_<n>.png
    """
    os.makedirs(out_dir, exist_ok=True)

    for epoch in sorted(epoch_stats.keys()):
        qstats = epoch_stats[epoch]

        # Queries sorted numerically
        query_ids = sorted(qstats.keys())

        probe_avg   = []
        transfer_avg = []
        gpu_avg     = []
        cpu_avg     = []
        qexec_avg   = []

        for qid in query_ids:
            metrics = qstats[qid]

            def avg_for(name):
                st = metrics.get(name, {"sum": 0, "count": 0})
                s = st["sum"]
                c = st["count"] if st["count"] > 0 else 1
                return s / c if c > 0 else 0.0

            probe_avg.append(avg_for("Probe time"))
            transfer_avg.append(avg_for("Transfer Time"))
            gpu_avg.append(avg_for("GPU Time"))
            cpu_avg.append(avg_for("CPU Time"))
            qexec_avg.append(avg_for("Query Execution Time"))

        # Bar positions
        x = np.arange(len(query_ids))
        width = 0.16

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(x - 2*width, probe_avg,   width, label="Probe time")
        ax.bar(x - width,  transfer_avg, width, label="Transfer Time")
        ax.bar(x,          gpu_avg,      width, label="GPU Time")
        ax.bar(x + width,  cpu_avg,      width, label="CPU Time")
        ax.bar(x + 2*width,qexec_avg,    width, label="Query Execution Time")

        ax.set_xlabel("Query ID")
        ax.set_ylabel("Average time (same units as log)")
        ax.set_title(f"Epoch {epoch}: per-query times")
        ax.set_xticks(x)
        ax.set_xticklabels([str(q) for q in query_ids])
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        plt.tight_layout()
        out_path = os.path.join(out_dir, f"epoch_{epoch}.png")
        plt.savefig(out_path)
        plt.close(fig)
        print(f"Wrote plot {out_path}")


def plot_per_query_across_epochs(epoch_stats, epoch_fraction, out_dir="query_plots"):
    """
    For each query id that appears in any epoch, create one plot:
      x-axis: fraction (cached fraction) for that query in each epoch
      y-axis: average Query Execution Time in that epoch
      one point per epoch that has both metrics.

    Output: query_plots/query_<qid>.png
    """
    os.makedirs(out_dir, exist_ok=True)

    # Collect all query ids seen anywhere
    all_qids = set()
    for epoch, qstats in epoch_stats.items():
        all_qids.update(qstats.keys())

    for qid in sorted(all_qids):
        epochs = []
        fractions = []
        qexec_avgs = []

        for epoch in sorted(epoch_stats.keys()):
            qstats = epoch_stats[epoch]
            if qid not in qstats:
                continue

            # Average Query Execution Time for this query in this epoch
            metrics = qstats[qid]
            qexec = metrics.get("Query Execution Time", {"sum": 0, "count": 0})
            s = qexec["sum"]
            c = qexec["count"]
            if c == 0:
                continue
            avg_qexec = s / c

            # Fraction for this query in this epoch
            frac_info = epoch_fraction.get(epoch, {}).get(qid, None)
            if not frac_info:
                continue

            epochs.append(epoch)
            fractions.append(frac_info["fraction"])
            qexec_avgs.append(avg_qexec)

        if not epochs:
            # nothing to plot for this query
            continue

        # Create scatter plot: x=fraction, y=avg Query Execution Time
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(fractions, qexec_avgs, c="tab:blue")

        for frac, qe, ep in zip(fractions, qexec_avgs, epochs):
            ax.annotate(str(ep), (frac, qe), textcoords="offset points",
                        xytext=(3, 3), fontsize=8)

        ax.set_xlabel("Cached fraction")
        ax.set_ylabel("Average Query Execution Time")
        ax.set_title(f"Query {qid}: fraction vs. Query Execution Time across epochs")
        ax.grid(True, linestyle="--", alpha=0.4)

        plt.tight_layout()
        out_path = os.path.join(out_dir, f"query_{qid}.png")
        plt.savefig(out_path)
        plt.close(fig)
        print(f"Wrote per-query plot {out_path}")


def main():
    epoch_stats, epoch_fraction = parse_log(LOG_PATH)
    total_epochs = len(epoch_stats)
    print(f"Parsed {total_epochs} epochs.")
    write_epoch_csvs(epoch_stats, epoch_fraction, LOG_PATH)

    # Per-epoch bar charts (one PNG per epoch)
    plot_epoch_metrics(epoch_stats)

    # Per-query scatter plots across epochs
    plot_per_query_across_epochs(epoch_stats, epoch_fraction)


if __name__ == "__main__":
    main()