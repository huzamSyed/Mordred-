
#!/usr/bin/env python3
# filepath: /home/huzam/Mordred/tools/rewrite_lineorder2_custkey.py
import os
import random
import struct
import tempfile

# HARD-CODED maximum c_custkey value (inclusive)
MAX_C_CUSTKEY = 157824740

# Path to the LINEORDER2 binary column file
LINEORDER2_PATH = "/home/huzam/Mordred/test/ssb/data/s160_columnar_copy/LINEORDER2"  # adjust if needed

# 4-byte little-endian signed int
INT_FMT = "<i"
INT_SIZE = struct.calcsize(INT_FMT)

def main():
    if not os.path.isfile(LINEORDER2_PATH):
        raise FileNotFoundError(f"LINEORDER2 file not found: {LINEORDER2_PATH}")

    size_bytes = os.path.getsize(LINEORDER2_PATH)
    if size_bytes % INT_SIZE != 0:
        raise RuntimeError(
            f"File size {size_bytes} is not a multiple of {INT_SIZE} bytes; "
            f"not a pure int32 column?"
        )

    num_rows = size_bytes // INT_SIZE
    print(f"Detected {num_rows} rows in LINEORDER2 "
          f"({size_bytes} bytes, {INT_SIZE}-byte ints).")
    print(f"Rewriting with uniform random keys in [1, {MAX_C_CUSTKEY}]")

    dir_name = os.path.dirname(LINEORDER2_PATH)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="LINEORDER2.new.", suffix=".bin")
    os.close(fd)

    try:
        with open(tmp_path, "wb") as out:
            pack = struct.pack
            for _ in range(num_rows):
                key = random.randint(1, MAX_C_CUSTKEY)
                out.write(pack(INT_FMT, key))

        os.replace(tmp_path, LINEORDER2_PATH)
        print("Successfully rewrote LINEORDER2 with new random foreign keys.")
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

if __name__ == "__main__":
    main()