#!/bin/bash
#SBATCH --job-name=data_gen
#SBATCH --ntasks=8
#SBATCH --output=data_gen%j.out
#SBATCH --time=12:00:00
#SBATCH --partition=low_unl_1gpu

mkdir results
for i in 1 10 20 40; do
  echo "bin/gpudb/test_${i} > results/${i}"
  bin/gpudb/test_${i} > results/${i}
done
