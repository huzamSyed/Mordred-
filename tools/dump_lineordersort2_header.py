
#!/usr/bin/env python3
# filepath: /home/huzam/Mordred/tools/dump_lineordersort2_header.py
import os
import struct

PATH = "/home/huzam/Mordred/test/ssb/data/s160_columnar_copy/LINEORDERSORT2"

def main():
    if not os.path.isfile(PATH):
        raise FileNotFoundError(PATH)

    with open(PATH, "rb") as f:
        # grab first 64 bytes, just to inspect
        hdr = f.read(64)
        print("First 64 bytes (hex):", hdr.hex())
        print("Length:", len(hdr))

        # Try a couple of plausible layouts to see what blockSize could be.
        # 1) original columnHeader from load.c (8,8,8,4,4,4)
        try:
            totalTupleNum, tupleNum, blockSize, fmt, blockId, blockTotal = struct.unpack("<qqqiii", hdr[:36])
            print("As <qqqiii> =>", totalTupleNum, tupleNum, blockSize, fmt, blockId, blockTotal)
        except Exception as e:
            print("Unpack <qqqiii> failed:", e)

        # 2) maybe all 32-bit:
        try:
            a, b, c, d = struct.unpack("<iiii", hdr[:16])
            print("As <iiii> =>", a, b, c, d)
        except Exception as e:
            print("Unpack <iiii> failed:", e)

if __name__ == "__main__":
    main()
