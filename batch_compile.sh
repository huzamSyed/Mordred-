#!/bin/bash
#SBATCH --job-name=data_gen
#SBATCH --ntasks=8
#SBATCH --output=data_gen%j.out
#SBATCH --time=12:00:00
#SBATCH --partition=low_unl_1gpu

for i in 1 10 20 40; do
  echo "Creating config:"
  ./mk_config.sh $i /home/karl/Code/Mordred_PLUS
  echo "Compiling"
  cmake --build build --target test --parallel 16
  mv bin/gpudb/test bin/gpudb/test_${i}
done
