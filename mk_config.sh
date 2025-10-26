#!/bin/bash
# Usage: ./mk_config.sh SF MOD_PATH

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Invalid Arguments"
  echo "Usage: ./mk_config.sh SF MOD_PATH"
  exit 1
fi

SF=${1}
MOD_PATH=${2}
BASE_PATH="${MOD_PATH}/test/ssb/data/"

case "$SF" in
1)
  DATA_DIR=${BASE_PATH}s1_columnar/
  LO_LEN=6001171
  P_LEN=200000
  S_LEN=2000
  C_LEN=30000
  D_LEN=2556
  ;;
10)
  DATA_DIR=${BASE_PATH}s10_columnar/
  LO_LEN=59986214
  P_LEN=800000
  S_LEN=20000
  C_LEN=300000
  D_LEN=2556
  ;;
20)
  DATA_DIR=${BASE_PATH}s20_columnar/
  LO_LEN=119994746
  P_LEN=1000000
  S_LEN=40000
  C_LEN=600000
  D_LEN=2556
  ;;
40)
  DATA_DIR=${BASE_PATH}s40_columnar/
  LO_LEN=240012412
  P_LEN=1200000
  S_LEN=80000
  C_LEN=1200000
  D_LEN=2556
  ;;
160)
  DATA_DIR=${BASE_PATH}s160_columnar/
  LO_LEN=960017453
  P_LEN=1600000
  S_LEN=320000
  C_LEN=4800000
  D_LEN=2556
  ;;
*)
  echo "Unknown SF: $SF" >&2
  exit 1
  ;;
esac

# cd test/ || exit
# cd ssb/dbgen/ || exit
# make || exit
# cd ../loader || exit
# make || exit

# cd ../../ || exit
# python util.py ssb $SF gen
# python util.py ssb $SF transform

# cd ssb/loader || exit
# make sort || exit
# ./columnSort ../data/s${SF}_columnar/LINEORDER ../data/s${SF}_columnar/LINEORDERSORT 5 16 ${C_LEN} || exit

# cd ../../../ || exit

  (
    echo "set(SF \"${SF}\")"
    echo "set(MOD_PATH \"${MOD_PATH}\")"
    echo "set(BASE_PATH \"${BASE_PATH}\")"
    echo "set(DATA_DIR \"${DATA_DIR}\")"
    echo "set(LO_LEN \"${LO_LEN}\")"
    echo "set(P_LEN \"${P_LEN}\")"
    echo "set(S_LEN \"${S_LEN}\")"
    echo "set(C_LEN \"${C_LEN}\")"
    echo "set(D_LEN \"${D_LEN}\")"
  ) | tee config.cmake
  (
    echo "SF=${SF}"
    echo "MOD_PATH=${MOD_PATH}"
    echo "BASE_PATH=${BASE_PATH}"
    echo "DATA_DIR=${DATA_DIR}"
    echo "LO_LEN=${LO_LEN}"
    echo "P_LEN=${P_LEN}"
    echo "S_LEN=${S_LEN}"
    echo "C_LEN=${C_LEN}"
    echo "D_LEN=${D_LEN}"
  ) | tee config.mk

