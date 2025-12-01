

import os
import sys
import struct
import subprocess

# Base dataset dirs (adjust if your tree is different)
BASE_DIR = os.path.join("test", "ssb", "data")
SRC_DIR_NAME = "s160_columnar"
DST_DIR_NAME = "s160_columnar_copy"

SRC_DIR = os.path.join(BASE_DIR, SRC_DIR_NAME)
DST_DIR = os.path.join(BASE_DIR, DST_DIR_NAME)
TMP_DIR = os.path.join(BASE_DIR, DST_DIR_NAME + "_tmp_date")

DATE_COLS = [
    "DDATE0",  # d_datekey
    "DDATE1",
    "DDATE2",
    "DDATE3",
]


def read_int32_column(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) % 4 != 0:
        raise RuntimeError(f"File size not multiple of 4 bytes: {path}")
    n = len(data) // 4
    return list(struct.unpack("<" + "i" * n, data))


def write_int32_column(path, values):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not values:
        open(path, "wb").close()
        return
    data = struct.pack("<" + "i" * len(values), *values)
    with open(path, "wb") as f:
        f.write(data)


def run_minmax():
    # Assumes minmax.sh is in the project root and uses DATA_DIR from ssb_utils.h
    print("Running minmax.sh ...")
    ret = subprocess.call(["bash", "minmax.sh"])
    if ret != 0:
        print(f"minmax.sh exited with status {ret}", file=sys.stderr)
        sys.exit(ret)
    print("minmax.sh completed")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <scale_factor>", file=sys.stderr)
        print(f"Example: {sys.argv[0]} 10", file=sys.stderr)
        sys.exit(1)

    scale = int(sys.argv[1])
    if scale <= 1:
        print("scale_factor must be > 1", file=sys.stderr)
        sys.exit(1)

    # 1) Read existing DDATE0 (d_datekey) from source dir
    ddate0_path = os.path.join(SRC_DIR, "DDATE0")
    print(f"Reading original DDATE0 from {ddate0_path}")
    date_src = read_int32_column(ddate0_path)
    n_src = len(date_src)
    print(f"Original rows in DDATE0: {n_src}")

    # 2) Build scaled DDATE0
    n_dst = n_src * scale
    date_dst = [0] * n_dst

    # Copy original
    date_dst[0:n_src] = date_src

    # Generate unique new keys for remaining rows
    max_key = max(date_src) if date_src else 0
    next_key = max_key + 1
    for i in range(n_src, n_dst):
        date_dst[i] = next_key
        next_key += 1

    print(f"Scaled rows in DDATE0: {n_dst}")
    print(f"New max d_datekey will be: {date_dst[-1]}")

    # 3) Write into TMP_DIR (only DDATE* there)
    os.makedirs(TMP_DIR, exist_ok=True)
    # Clean old DDATE* in TMP_DIR if any
    for col in DATE_COLS:
        p = os.path.join(TMP_DIR, col)
        if os.path.exists(p):
            os.remove(p)

    # Write scaled DDATE0
    write_int32_column(os.path.join(TMP_DIR, "DDATE0"), date_dst)

    # Write other DDATE columns as zeros
    for col in DATE_COLS:
        if col == "DDATE0":
            continue
        write_int32_column(os.path.join(TMP_DIR, col), [0] * n_dst)
        print(f"Wrote zero-filled column {col} with {n_dst} rows into {TMP_DIR}")

    print(f"Finished writing scaled date columns into {TMP_DIR}")

    # 4) Copy only DDATE* from TMP_DIR into DST_DIR (do NOT delete DST_DIR)
    os.makedirs(DST_DIR, exist_ok=True)
    for col in DATE_COLS:
        src = os.path.join(TMP_DIR, col)
        dst = os.path.join(DST_DIR, col)
        if os.path.exists(dst):
            os.remove(dst)
        os.replace(src, dst)
        print(f"Updated {dst}")

    print(f"Updated DDATE0..3 in {DST_DIR}")

    # 5) Run minmax.sh (assumes DATA_DIR points at DST_DIR in ssb_utils.h)
    run_minmax()

    print("All done.")
    print(f"Scaled date in: {DST_DIR}")
    print(f"Rows in DDATE0: {n_dst}")
    print(f"Final DDATE0 max d_datekey: {date_dst[-1]}")


if __name__ == "__main__":
    main()