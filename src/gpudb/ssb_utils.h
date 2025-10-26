#pragma once

#include <iostream>
#include <fstream>
#include <string>

/*#include <cuda.h>*/
/*#include <cub/util_allocator.cuh>*/
#include <cuda.h>
#include <curand.h>
#include <cub/util_allocator.cuh>

#include "ssb_utils_cpu.h"

using namespace std;


template<typename T>
T* loadColumnPinned(string col_name, int num_entries) {
  T* h_col;
  CubDebugExit(cudaHostAlloc((void**) &h_col, ((num_entries + SEGMENT_SIZE - 1)/SEGMENT_SIZE) * SEGMENT_SIZE * sizeof(T), cudaHostAllocDefault));
  string filename = DATA_DIR + lookup(col_name);
  ifstream colData (filename.c_str(), ios::in | ios::binary);
  if (!colData) {
    return NULL;
  }

  colData.read((char*)h_col, num_entries * sizeof(T));
  return h_col;
}

template<typename T>
T* loadColumnPinnedSort(string col_name, int num_entries) {
  T* h_col;
  CubDebugExit(cudaHostAlloc((void**) &h_col, ((num_entries + SEGMENT_SIZE - 1)/SEGMENT_SIZE) * SEGMENT_SIZE * sizeof(T), cudaHostAllocDefault));
  string filename = DATA_DIR + lookupSort(col_name);
  ifstream colData (filename.c_str(), ios::in | ios::binary);
  if (!colData) {
    return NULL;
  }

  colData.read((char*)h_col, num_entries * sizeof(T));
  return h_col;
}
