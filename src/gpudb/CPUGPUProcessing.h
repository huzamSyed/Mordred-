#ifndef _CPUGPU_PROCESSING_H_
#define _CPUGPU_PROCESSING_H_

#include "QueryOptimizer.h"
#include "GPUProcessing.h"
#include "CPUProcessing.h"
#include "common.h"

#define OD_BATCH_SIZE 8

struct times {
    double pfilter_probe_gpu = 0;
    double pfilter_probe_cpu = 0;
    double probe_group_gpu = 0;
    double probe_group_cpu = 0;
    double probe_gpu = 0;
    double probe_cpu = 0;
    double pfilter_gpu = 0;
    double pfilter_cpu = 0;
    double bfilter_build_gpu = 0;
    double bfilter_build_cpu = 0;
    double build_gpu = 0;
    double build_cpu = 0;
    double bfilter_gpu = 0;
    double bfilter_cpu = 0;
    double group_gpu = 0;
    double group_cpu = 0;
    double agg_gpu = 0;
    double agg_cpu = 0;
    double probe_agg_gpu = 0;
    double probe_agg_cpu = 0;
    double pfilter_probe_agg_gpu = 0;
    double pfilter_probe_agg_cpu = 0;

    void print() const {
        auto print_if_nonzero = [](const char* name, float value) {
            if (value != 0.0f)
                std::cout << name << ": " << value << "\n";
        };

        print_if_nonzero("pfilter_probe_gpu", pfilter_probe_gpu);
        print_if_nonzero("pfilter_probe_cpu", pfilter_probe_cpu);
        print_if_nonzero("probe_group_gpu", probe_group_gpu);
        print_if_nonzero("probe_group_cpu", probe_group_cpu);
        print_if_nonzero("probe_gpu", probe_gpu);
        print_if_nonzero("probe_cpu", probe_cpu);
        print_if_nonzero("pfilter_gpu", pfilter_gpu);
        print_if_nonzero("pfilter_cpu", pfilter_cpu);
        print_if_nonzero("bfilter_build_gpu", bfilter_build_gpu);
        print_if_nonzero("bfilter_build_cpu", bfilter_build_cpu);
        print_if_nonzero("build_gpu", build_gpu);
        print_if_nonzero("build_cpu", build_cpu);
        print_if_nonzero("bfilter_gpu", bfilter_gpu);
        print_if_nonzero("bfilter_cpu", bfilter_cpu);
        print_if_nonzero("group_gpu", group_gpu);
        print_if_nonzero("group_cpu", group_cpu);
        print_if_nonzero("agg_gpu", agg_gpu);
        print_if_nonzero("agg_cpu", agg_cpu);
        print_if_nonzero("probe_agg_gpu", probe_agg_gpu);
        print_if_nonzero("probe_agg_cpu", probe_agg_cpu);
        print_if_nonzero("pfilter_probe_agg_gpu", pfilter_probe_agg_gpu);
        print_if_nonzero("pfilter_probe_agg_cpu", pfilter_probe_agg_cpu);
    }

    void reset() {
        *this = times();
    }
};

class CPUGPUProcessing {
public:
  CacheManager* cm;
  QueryOptimizer* qo;

  times times;
  bool custom;
  bool skipping;

  int** col_idx;
  // int** od_col_idx;
  chrono::high_resolution_clock::time_point begin_time;
  bool verbose;

  double transfer_time_total;
  double cpu_time_total;
  double gpu_time_total;
  double malloc_time_total;

  double* transfer_time;
  double* cpu_time;
  double* gpu_time;
  double* malloc_time;

  unsigned long long* cpu_to_gpu;
  unsigned long long* gpu_to_cpu;

  unsigned long long cpu_to_gpu_total;
  unsigned long long gpu_to_cpu_total;

  double execution_total;
  double optimization_total;
  double merging_total;

  CPUGPUProcessing(size_t _cache_size, size_t _processing_size, size_t _pinned_memsize, bool _verbose, bool _custom = true, bool _skipping = true, double alpha = 0.1);

  ~CPUGPUProcessing() {
    delete[] col_idx;
    delete[] transfer_time;
    delete[] cpu_time;
    delete[] gpu_time;
    delete[] malloc_time;

    delete[] cpu_to_gpu;
    delete[] gpu_to_cpu;
    delete qo;
  }

  void resetCGP() {
    for (int i = 0; i < cm->TOT_COLUMN; i++) {
      if (col_idx[i] != NULL && !custom) cudaFree(col_idx);
      col_idx[i] = NULL;
    }
  }

  void resetTime();

  void switch_device_fact(int** &off_col, int** &h_off_col, int* &d_total, int* h_total, int sg, int mode, int table, cudaStream_t stream);

  void call_pfilter_probe_GPU(QueryParams* params, int** &off_col, int* &d_total, int* h_total, int sg, int select_so_far, cudaStream_t stream);

  void call_pfilter_probe_CPU(QueryParams* params, int** &h_off_col, int* h_total, int sg, int select_so_far);

  void call_probe_group_by_GPU(QueryParams* params, int** &off_col, int* h_total, int sg, cudaStream_t stream);

  void call_probe_group_by_CPU(QueryParams* params, int** &h_off_col, int* h_total, int sg);

  void call_probe_GPU(QueryParams* params, int** &off_col, int* &d_total, int* h_total, int sg, cudaStream_t stream);

  void call_probe_CPU(QueryParams* params, int** &h_off_col, int* h_total, int sg);

  void call_pfilter_GPU(QueryParams* params, int** &off_col, int* &d_total, int* h_total, int sg, int select_so_far, cudaStream_t stream);

  void call_pfilter_CPU(QueryParams* params, int** &h_off_col, int* h_total, int sg, int select_so_far);



  void switch_device_dim(int* &off_col, int* &h_off_col, int* &d_total, int* h_total, int sg, int mode, int table, cudaStream_t stream);

  void call_bfilter_build_GPU(QueryParams* params, int* &d_off_col, int* h_total, int sg, int table, cudaStream_t stream);

  void call_bfilter_build_CPU(QueryParams* params, int* &h_off_col, int* h_total, int sg, int table);

  void call_build_GPU(QueryParams* params, int* &d_off_col, int* h_total, int sg, int table, cudaStream_t stream);

  void call_build_CPU(QueryParams* params, int* &h_off_col, int* h_total, int sg, int table);

  void call_bfilter_GPU(QueryParams* params, int* &d_off_col, int* &d_total, int* h_total, int sg, int table, cudaStream_t stream);

  void call_bfilter_CPU(QueryParams* params, int* &h_off_col, int* h_total, int sg, int table);



  void call_group_by_GPU(QueryParams* params, int** &off_col, int* h_total, int sg, cudaStream_t stream);

  void call_group_by_CPU(QueryParams* params, int** &h_off_col, int* h_total, int sg);

  void call_aggregation_GPU(QueryParams* params, int* &off_col, int* h_total, int sg, cudaStream_t stream);

  void call_aggregation_CPU(QueryParams* params, int* &h_off_col, int* h_total, int sg);

  void call_probe_aggr_GPU(QueryParams* params, int** &off_col, int* h_total, int sg, cudaStream_t stream);

  void call_probe_aggr_CPU(QueryParams* params, int** &h_off_col, int* h_total, int sg);

  void call_pfilter_probe_aggr_GPU(QueryParams* params, int** &off_col, int* h_total, int sg, int select_so_far, cudaStream_t stream);

  void call_pfilter_probe_aggr_CPU(QueryParams* params, int** &h_off_col, int* h_total, int sg, int select_so_far);

  void copyColIdx();
};

#endif
