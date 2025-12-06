#include "CPUGPUProcessing.h"
#include "CPUProcessing.h"
#include "CacheManager.h"
#include "CostModel.h"
#include "QueryOptimizer.h"
#include "QueryProcessing.h"

int main() {

  cudaSetDevice(0);
  CUdevice device;
  cuDeviceGet(&device, 0);

  bool verbose = 1;

  srand(123);

  size_t size = 52428800 * 20;      // 200 MB
  size_t processing = 52428800 * 7; // 400MB
  size_t pinned = 52428800 * 20;    // 400MB
  double alpha = 1.0;
  bool custom = true;
  bool skipping = true;

  cout << "Allocating " << size * 4 / 1024 / 1024 << " MB GPU Cache and "
       << processing * 8 / 1024 / 1024 << " MB GPU Processing Region" << endl;

  CPUGPUProcessing *cgp =
      new CPUGPUProcessing(size, processing, pinned, verbose, custom, skipping);
  QueryProcessing *qp;

  cout << endl;

  bool exit = 0;
  string input, query, many, policy;
  int many_query;
  ReplacementPolicy repl_policy;
  double time = 0;
  double malloc_time_total = 0, execution_time = 0, optimization_time = 0,
         merging_time = 0;
  double time1 = 0, time2 = 0;
  unsigned long long cpu_to_gpu = 0, gpu_to_cpu = 0;
  unsigned long long cpu_to_gpu1 = 0, gpu_to_cpu1 = 0;
  unsigned long long cpu_to_gpu2 = 0, gpu_to_cpu2 = 0;
  unsigned long long repl_traffic = 0;
  double malloc_time_total1 = 0, execution_time1 = 0, optimization_time1 = 0,
         merging_time1 = 0;
  double malloc_time_total2 = 0, execution_time2 = 0, optimization_time2 = 0,
         merging_time2 = 0;
  Distribution dist = None;
  double mean = 1;

  qp = new QueryProcessing(cgp, verbose, dist);


    time = 0;
    malloc_time_total = 0;
    cpu_to_gpu = 0;
    gpu_to_cpu = 0;
    execution_time = 0;
    optimization_time = 0;
    merging_time = 0;
    repl_traffic = 0;
    repl_policy = ReplacementPolicy::Segmented;

    cgp->resetTime();

    for (int i = 0; i < 100; i++) {
      qp->generate_rand_query();
      time1 = qp->processQuery();
      cgp->resetTime();
    }
    cgp->cm->runReplacement(repl_policy);

    cout << "\n\n\n**********\n" << flush;
    auto times = cgp->times;
    auto times1 = times;
    auto times2 = times1;

    for (int iter = 0; iter < 20; iter++) {
      for (int i = 1; i < 16*4; i++) {
        cout << "Running Query: " << flush;
        qp->generate_rand_query();

        std::cout << "Query Part 1" << std::endl;
        time1 = qp->processQuery();
        malloc_time_total1 = cgp->malloc_time_total;
        cpu_to_gpu1 = cgp->cpu_to_gpu_total;
        gpu_to_cpu1 = cgp->gpu_to_cpu_total;
        execution_time1 = cgp->execution_total;
        optimization_time1 = cgp->optimization_total;
        merging_time1 = cgp->merging_total;
        cout << "\nTiming Info Start\n" << flush;
        cgp->times.print();
        cout << "\nTiming Info End\n" << flush;
        cgp->resetTime();
        std::cout << "Completed Part 1" << std::endl;

        std::cout << "Query Part 2" << std::endl;
        time2 = qp->processQuery2();
        malloc_time_total2 = cgp->malloc_time_total;
        cpu_to_gpu2 = cgp->cpu_to_gpu_total;
        gpu_to_cpu2 = cgp->gpu_to_cpu_total;
        execution_time2 = cgp->execution_total;
        optimization_time2 = cgp->optimization_total;
        merging_time2 = cgp->merging_total;
        cout << "\nTiming Info Start\n" << flush;
        cgp->times.print();
        cout << "\nTiming Info End\n" << flush;
        cgp->resetTime();
        std::cout << "Completed Part 2" << std::endl;

        int which = 1;

        if (time1 <= time2) {
          time += time1;
          times = times1;
          cpu_to_gpu += cpu_to_gpu1;
          gpu_to_cpu += gpu_to_cpu1;
          malloc_time_total += malloc_time_total1;
          execution_time += execution_time1;
          optimization_time += optimization_time1;
          merging_time += merging_time1;
        } else {
          which = 2;
          time += time2;
          times = times2;
          cpu_to_gpu += cpu_to_gpu2;
          gpu_to_cpu += gpu_to_cpu2;
          malloc_time_total += malloc_time_total2;
          execution_time += execution_time2;
          optimization_time += optimization_time2;
          merging_time += merging_time2;
        }
        cout << "Completed Query, used part " << which << endl;
      }
      cout << "Epoch Complete, Running replacement" << endl;

      cgp->cm->runReplacement(repl_policy, &repl_traffic);
      qp->percentageData();
      if (repl_policy == Segmented || repl_policy == LFUSegmented)
        cgp->cm->newEpoch(0.5);
      if (repl_policy == LRU2Segmented)
        cgp->cm->newEpoch(2.0);
    }

    cout << "Replacement traffic: " << repl_traffic << endl;
    srand(123);

    cout << endl;
    cout << "Cumulated Time: " << time << endl;
    cout << "Execution time: " << execution_time << endl;
    cout << endl;
}
