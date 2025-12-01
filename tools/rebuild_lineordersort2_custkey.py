
#!/usr/bin/env python3
# filepath: /home/huzam/Mordred/tools/rebuild_lineordersort2_custkey.py
import os
import random
import struct
import tempfile

# Hard-coded maximum c_custkey (inclusive)
MAX_C_CUSTKEY = 157824740

# Paths – adjust if needed
LINEORDER2_PATH     = "/home/huzam/Mordred/test/ssb/data/s160_columnar_copy/LINEORDER2"
LINEORDERSORT2_PATH = "/home/huzam/Mordred/test/ssb/data/s160_columnar_copy/LINEORDERSORT2"

# columnHeader from loader/include/common.h
# long totalTupleNum;
# long tupleNum;
# long blockSize;
# int  format;
# int  blockId;
# int  blockTotal;
HEADER_FMT  = "<qqqiii"
HEADER_SIZE = struct.calcsize(HEADER_FMT)

INT_FMT  = "<i"
INT_SIZE = struct.calcsize(INT_FMT)

def get_tuple_count_from_lineorder2():
    if not os.path.isfile(LINEORDER2_PATH):
        raise FileNotFoundError(LINEORDER2_PATH)
    with open(LINEORDER2_PATH, "rb") as f:
        hdr = f.read(HEADER_SIZE)
        if len(hdr) != HEADER_SIZE:
            raise RuntimeError("LINEORDER2: truncated header")
        totalTupleNum, tupleNum, blockSize, fmt, blockId, blockTotal = struct.unpack(
            HEADER_FMT, hdr
        )
        # Do NOT enforce fmt here; we just need totalTupleNum
        return totalTupleNum

def main():
    total_tuples = get_tuple_count_from_lineorder2()
    print(f"Detected {total_tuples} rows from LINEORDER2")
    print(f"Rebuilding LINEORDERSORT2 with random keys in [1, {MAX_C_CUSTKEY}]")

    dir_name = os.path.dirname(LINEORDERSORT2_PATH)
    fd, tmp_path = tempfile.mkstemp(
        dir=dir_name, prefix="LINEORDERSORT2.new.", suffix=".bin"
    )
    os.close(fd)

    try:
        with open(tmp_path, "wb") as out:
            # Single-block, uncompressed column
            totalTupleNum = total_tuples
            tupleNum      = total_tuples
            blockSize     = total_tuples * INT_SIZE
            fmt           = 0          # pretend UNCOMPRESSED
            blockId       = 0
            blockTotal    = 1

            header_bytes = struct.pack(
                HEADER_FMT,
                totalTupleNum,
                tupleNum,
                blockSize,
                fmt,
                blockId,
                blockTotal,
            )
            out.write(header_bytes)

            pack = struct.pack
            for _ in range(total_tuples):
                key = random.randint(1, MAX_C_CUSTKEY)
                out.write(pack(INT_FMT, key))

        os.replace(tmp_path, LINEORDERSORT2_PATH)
        print("Successfully rebuilt LINEORDERSORT2 as a random int32 column.")
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

if __name__ == "__main__":
    main()