
# filepath: /home/huzam/Mordred/tools/scale_customer.py
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
TMP_DIR = os.path.join(BASE_DIR, DST_DIR_NAME + "_tmp")

CUSTOMER_COLS = [
    "CUSTOMER0",
    "CUSTOMER1",
    "CUSTOMER2",
    "CUSTOMER3",
    "CUSTOMER4",
    "CUSTOMER5",
    "CUSTOMER6",
    "CUSTOMER7",
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

    # 1) Read existing CUSTOMER0 from source dir
    cust0_path = os.path.join(SRC_DIR, "CUSTOMER0")
    print(f"Reading original CUSTOMER0 from {cust0_path}")
    cust_src = read_int32_column(cust0_path)
    n_src = len(cust_src)
    print(f"Original rows in CUSTOMER0: {n_src}")

    # 2) Build scaled CUSTOMER0
    n_dst = n_src * scale
    cust_dst = [0] * n_dst

    # Copy original
    cust_dst[0:n_src] = cust_src

    # Generate unique new keys for remaining rows
    max_key = max(cust_src) if cust_src else 0
    next_key = max_key + 1
    for i in range(n_src, n_dst):
        cust_dst[i] = next_key
        next_key += 1

    print(f"Scaled rows in CUSTOMER0: {n_dst}")
    print(f"New max key will be: {cust_dst[-1]}")

    # 3) Write into TMP_DIR (only CUSTOMER* there)
    os.makedirs(TMP_DIR, exist_ok=True)
    # Clean old CUSTOMER* in TMP_DIR if any
    for col in CUSTOMER_COLS:
        p = os.path.join(TMP_DIR, col)
        if os.path.exists(p):
            os.remove(p)

    # Write scaled CUSTOMER0
    write_int32_column(os.path.join(TMP_DIR, "CUSTOMER0"), cust_dst)

    # Write other CUSTOMER columns as zeros
    for col in CUSTOMER_COLS:
        if col == "CUSTOMER0":
            continue
        write_int32_column(os.path.join(TMP_DIR, col), [0] * n_dst)
        print(f"Wrote zero-filled column {col} with {n_dst} rows into {TMP_DIR}")

    print(f"Finished writing scaled customer columns into {TMP_DIR}")

    # 4) Copy only CUSTOMER* from TMP_DIR into DST_DIR (do NOT delete DST_DIR)
    os.makedirs(DST_DIR, exist_ok=True)
    for col in CUSTOMER_COLS:
        src = os.path.join(TMP_DIR, col)
        dst = os.path.join(DST_DIR, col)
        if os.path.exists(dst):
            os.remove(dst)
        os.replace(src, dst)
        print(f"Updated {dst}")

    print(f"Updated CUSTOMER0..7 in {DST_DIR}")

    # 5) Run minmax.sh (assumes DATA_DIR points at DST_DIR in ssb_utils.h)
    run_minmax()

    print("All done.")
    print(f"Scaled customer in: {DST_DIR}")
    print(f"Rows in CUSTOMER0: {n_dst}")
    print(f"Final CUSTOMER0 max key: {cust_dst[-1]}")


if __name__ == "__main__":
    main()