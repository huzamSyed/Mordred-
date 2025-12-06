#!/bin/bash
#SBATCH --job-name=data_gen
#SBATCH --ntasks=8
#SBATCH --output=data_gen%j.out
#SBATCH --time=12:00:00
#SBATCH --partition=low_unl_1gpu

for i in 1 10 20 40 15; do
  echo "Creating config and data"
  ./mk_config.sh $i /home/karl/Code/Mordred_PLUS yes
  echo "Making minmax"
  cmake --build build --target minmax minmaxsort --parallel 16
  echo "Populating minmax"
  ./minmax.sh
done
