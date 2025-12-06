#!/usr/bin/env python3

import sys
import os
import re
from collections import defaultdict

def main():
    # output root directory from CLI, default "queries"
    OUTPUT_ROOT = sys.argv[1] if len(sys.argv) > 1 else "queries"

    data = sys.stdin.read()
    if not data.strip():
        print("No input on stdin.", file=sys.stderr)
        return

    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    #
    # TOP-LEVEL BLOCKS:
    # Running Query: <num>
    #    ... Query Part 1 ... Completed Part 1
    #    ... Query Part 2 ... Completed Part 2
    # Completed Query, used part <x>
    #
    # (?s) = DOTALL
    #
    top_pattern = r"(?s)Running Query:\s*(\d+)(.*?)(?:Completed Query,\s*used part\s*(\d+))"
    top_blocks = re.findall(top_pattern, data)

    if not top_blocks:
        print("No top-level query blocks found.", file=sys.stderr)
        return

    # independent entry counters per query number
    counters = defaultdict(int)

    for qnum, body, used_part in top_blocks:
        used_part = used_part.strip()
        
        # Extract the two subparts inside each query block
        sub_pattern = r"(?s)Query Part\s*(1|2)(.*?)Completed Part\s*\1"
        parts = {pnum: content for pnum, content in re.findall(sub_pattern, body)}

        if used_part not in parts:
            print(f"Warning: Query {qnum} indicates used part {used_part} but that part was not found.",
                  file=sys.stderr)
            continue

        selected_content = parts[used_part].strip()

        # Update entry counter for this query
        counters[qnum] += 1
        entry_num = counters[qnum]

        # Create directory queries/<qnum>/
        qdir = os.path.join(OUTPUT_ROOT, qnum)
        os.makedirs(qdir, exist_ok=True)

        out_file = os.path.join(qdir, f"entry_{entry_num}.txt")

        # Write only the selected part
        with open(out_file, "w") as f:
            f.write(selected_content + "\n")

        print(f"Saved {out_file} (used part {used_part})", file=sys.stderr)


if __name__ == "__main__":
    main()
