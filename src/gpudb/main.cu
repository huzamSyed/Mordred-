#include "QueryProcessing.h"
#include "QueryOptimizer.h"
#include "CPUGPUProcessing.h"
#include "CacheManager.h"
#include "CPUProcessing.h"
#include "CostModel.h"
#include <sys/time.h>
double current_time_1() {
    struct timeval tv;
    gettimeofday(&tv, nullptr);
    return static_cast<double>(tv.tv_sec) * 1000.0 +
           static_cast<double>(tv.tv_usec) / 1000.0;
}
int main() {

	cudaSetDevice(0);
	CUdevice device;
	cuDeviceGet(&device, 0);

	bool verbose = 1;

	srand(123);
   int C = 20 ; 
	size_t size = 52428800ULL * 5*C; //200 MB
	size_t processing = 52428800ULL * 15*4; //400MB
	size_t pinned = 52428800ULL * 5*C*8; //400MB
	double alpha = 1.0;
	bool custom = true;
	bool skipping = true;

	cout << "Alloc ating " << size * 4 / 1024 / 1024 <<" MB GPU Cache and " << processing * 8 / 1024 / 1024 << " MB GPU Processing Region" << endl;
	
	CPUGPUProcessing* cgp = new CPUGPUProcessing(size, processing, pinned, verbose, custom, skipping);
	QueryProcessing* qp;

	cout << endl;

	bool exit = 0;
	string input, query, many, policy;
	int many_query;
	ReplacementPolicy repl_policy;
	double time = 0;
	double malloc_time_total = 0, execution_time = 0, optimization_time = 0, merging_time = 0;
	double time1 = 0, time2 = 0;
	unsigned long long cpu_to_gpu = 0, gpu_to_cpu = 0;
	unsigned long long cpu_to_gpu1 = 0, gpu_to_cpu1 = 0;
	unsigned long long cpu_to_gpu2 = 0, gpu_to_cpu2 = 0;
	unsigned long long repl_traffic = 0;
	double malloc_time_total1 = 0, execution_time1 = 0, optimization_time1 = 0, merging_time1 = 0;
	double malloc_time_total2 = 0, execution_time2 = 0, optimization_time2 = 0, merging_time2 = 0;
	Distribution dist = None;
	double mean = 1;

	qp = new QueryProcessing(cgp, verbose, dist);

	while (!exit) {
		cout << "Select Options:" << endl;
		cout << "1. Run Specific Query" << endl;
		cout << "2. Run Random Queries" << endl;
		cout << "3. Run Experiment" << endl;
		cout << "4. Replacement" << endl;
		cout << "5. Dump Trace" << endl;
		cout << "6. Exit" << endl;
		cout << "cache. Cache Specific Column" << endl;
		cout << "clear. Delete Columns from GPU" << endl;
		cout << "custom. Toggle custom malloc" << endl;
		cout << "skipping. Toggle segment skipping" << endl;
		cout << "Your Input: ";
		cin >> input;

		if (input.compare("1") == 0) {
			time = 0; malloc_time_total = 0; cpu_to_gpu = 0; gpu_to_cpu = 0; execution_time = 0; optimization_time = 0; merging_time = 0;
			cgp->resetTime();
			cout << "Input Query: ";
			cin >> query;
			qp->setQuery(stoi(query));
            long long lo_extended_price  ;
			//cin>>lo_extended_price ; 
			qp->lo_extended_price = lo_extended_price ; 
			time1 = qp->processQuery();
			malloc_time_total1 = cgp->malloc_time_total;
			cpu_to_gpu1 = cgp->cpu_to_gpu_total;
			gpu_to_cpu1 = cgp->gpu_to_cpu_total;
			execution_time1 = cgp->execution_total;
			optimization_time1 = cgp->optimization_total;
			merging_time1 = cgp->merging_total;
			cgp->resetTime();
        
			time2 = qp->processQuery2();
			malloc_time_total2 = cgp->malloc_time_total;
			cpu_to_gpu2 = cgp->cpu_to_gpu_total;
			gpu_to_cpu2 = cgp->gpu_to_cpu_total;
			execution_time2 = cgp->execution_total;
			optimization_time2 = cgp->optimization_total;
			merging_time2 = cgp->merging_total;
			cgp->resetTime();

			if (time1 <= time2) {
				time += time1; cpu_to_gpu += cpu_to_gpu1; gpu_to_cpu += gpu_to_cpu1; malloc_time_total += malloc_time_total1;
				execution_time += execution_time1; optimization_time += optimization_time1; merging_time += merging_time1;
			} else {
				time += time2; cpu_to_gpu += cpu_to_gpu2; gpu_to_cpu += gpu_to_cpu2; malloc_time_total += malloc_time_total2;
				execution_time += execution_time2; optimization_time += optimization_time2; merging_time += merging_time2;
			}

		} else if (input.compare("2") == 0) {
			time = 0; malloc_time_total = 0; cpu_to_gpu = 0; gpu_to_cpu = 0; execution_time = 0; optimization_time = 0; merging_time = 0;
			cout << "How many queries: ";
			cin >> many;
			many_query = stoi(many);
			cgp->resetTime();
			cout << "Executing Random Query" << endl;
			for (int i = 0; i < many_query; i++) {
				qp->generate_rand_query();

				time1 = qp->processQuery();
				malloc_time_total1 = cgp->malloc_time_total;
				cpu_to_gpu1 = cgp->cpu_to_gpu_total;
				gpu_to_cpu1 = cgp->gpu_to_cpu_total;
				execution_time1 = cgp->execution_total;
				optimization_time1 = cgp->optimization_total;
				merging_time1 = cgp->merging_total;
				cgp->resetTime();

				time2 = qp->processQuery2();
				malloc_time_total2 = cgp->malloc_time_total;
				cpu_to_gpu2 = cgp->cpu_to_gpu_total;
				gpu_to_cpu2 = cgp->gpu_to_cpu_total;
				execution_time2 = cgp->execution_total;
				optimization_time2 = cgp->optimization_total;
				merging_time2 = cgp->merging_total;
				cgp->resetTime();

				if (time1 <= time2) {
					time += time1; cpu_to_gpu += cpu_to_gpu1; gpu_to_cpu += gpu_to_cpu1; malloc_time_total += malloc_time_total1;
					execution_time += execution_time1; optimization_time += optimization_time1; merging_time += merging_time1;
				} else {
					time += time2; cpu_to_gpu += cpu_to_gpu2; gpu_to_cpu += gpu_to_cpu2; malloc_time_total += malloc_time_total2;
					execution_time += execution_time2; optimization_time += optimization_time2; merging_time += merging_time2;
				}
				
			}
			srand(123);
		} else if (input.compare("3") == 0) {
			time = 0; malloc_time_total = 0; cpu_to_gpu = 0; gpu_to_cpu = 0; execution_time = 0; optimization_time = 0; merging_time = 0;
			repl_traffic = 0;
			cout << "How many queries per  epoch (20 epoch in total): ";
			cin >> many;
			many_query = stoi(many);

			cout << "Replacement Policy: ";
			cin >> policy;

			if (policy == "LRU") {
				repl_policy = LRU;
			} else if (policy == "LFU") {
				repl_policy = LFU;
			} else if (policy == "LRUSegmented") {
				repl_policy = LRUSegmented;
			} else if (policy == "LFUSegmented") {
				repl_policy = LFUSegmented;
			} else if (policy == "LRU2") {
				repl_policy = LRU2;
			} else if (policy == "LRU2Segmented") {
				repl_policy = LRU2Segmented;
			} else if (policy == "SemanticAware") {
				repl_policy = Segmented;
			} else {
				repl_policy = Segmented;
			}

			cgp->resetTime();

			// if (dist != Norm) {
				cout << "Warmup" << endl;
				for (int i = 0; i < 100; i++) {
					qp->generate_rand_query();
					time1 = qp->processQuery();
					cgp->resetTime();
				}
				cgp->cm->runReplacement(repl_policy);				
			// }


			cout << "Run Experiment" << endl;


			for (int iter = 0; iter < 20; iter++) {
                cout<<" epoch start "<<endl;  
				for (int i = 0; i < many_query; i++) {
					qp->generate_rand_query();

					time1 = qp->processQuery();
					malloc_time_total1 = cgp->malloc_time_total;
					cpu_to_gpu1 = cgp->cpu_to_gpu_total;
					gpu_to_cpu1 = cgp->gpu_to_cpu_total;
					execution_time1 = cgp->execution_total;
					optimization_time1 = cgp->optimization_total;
					merging_time1 = cgp->merging_total;
					cgp->resetTime();

					// time2 = qp->processQuery2();
					// malloc_time_total2 = cgp->malloc_time_total;
					// cpu_to_gpu2 = cgp->cpu_to_gpu_total;
					// gpu_to_cpu2 = cgp->gpu_to_cpu_total;
					// execution_time2 = cgp->execution_total;
					// optimization_time2 = cgp->optimization_total;
					// merging_time2 = cgp->merging_total;
					// cgp->resetTime();

					if (1) {
						time += time1; cpu_to_gpu += cpu_to_gpu1; gpu_to_cpu += gpu_to_cpu1; malloc_time_total += malloc_time_total1;
						execution_time += execution_time1; optimization_time += optimization_time1; merging_time += merging_time1;
					} else {
						time += time2; cpu_to_gpu += cpu_to_gpu2; gpu_to_cpu += gpu_to_cpu2; malloc_time_total += malloc_time_total2;
						execution_time += execution_time2; optimization_time += optimization_time2; merging_time += merging_time2;
					}


				}				

				cgp->cm->runReplacement(repl_policy, &repl_traffic);
				qp->percentageData();
				cout<<" epoch end"<<endl; 
				if (repl_policy == Segmented || repl_policy == LFUSegmented) cgp->cm->newEpoch(0.5);
				if (repl_policy == LRU2Segmented) cgp->cm->newEpoch(2.0);


			}

			cout << "Replacement traffic: " << repl_traffic << endl;

			srand(123);

		} else if (input.compare("4") == 0) {
			cout << "Replacement Policy: ";
			cin >> policy;

			if (policy == "LRU") {
				repl_policy = LRU;
			} else if (policy == "LFU") {
				repl_policy = LFU;
			} else if (policy == "LRUSegmented") {
				repl_policy = LRUSegmented;
			} else if (policy == "LFUSegmented") {
				repl_policy = LFUSegmented;
			} else if (policy == "LRU2") {
				repl_policy = LRU2;
			} else if (policy == "LRU2Segmented") {
				repl_policy = LRU2Segmented;
			} else if (policy == "SemanticAware") {
				repl_policy = Segmented;
			}

			cgp->cm->runReplacement(repl_policy);
			qp->percentageData();
			srand(123);
		} else if (input.compare("5") == 0) {
			string filename;
			cout << "File name:  ";
			cin >> filename;
			qp->dumpTrace("logs/"+filename);
			cout << "Dumped Trace" << endl;
		} else if (input.compare("cache") == 0) {
			string column_name;
			int ret;
			do {
				cout << "	Column to cache: ";
				cin >> column_name;
				int segments_to_cache ; 
				cout<<" enter the number of segments to be cahced "<<endl; 
				cin>> segments_to_cache ; 
				double s = current_time_1() ; 
				ret = cgp->cm->cacheSpecificColumn(column_name,segments_to_cache);
				double e = current_time_1() ; 
				cout<<" Time to cache the column  "<< column_name <<" is  "<< (e -s) << " seconds "<<endl;
			} while (ret != 0);
		} else if (input.compare("clear") == 0) {
			cgp->cm->deleteAll();
		} else if (input.compare("skipping") == 0) {
			skipping = !skipping;
			cgp->skipping = skipping;
			cgp->qo->skipping = skipping;
			qp->skipping = skipping;
			if (skipping) cout << "Segment skipping is enabled" << endl;
			else cout << "Segment skipping is disabled" << endl;
		} else if (input.compare("custom") == 0) {
			custom = !custom;
			cgp->custom = custom;
			cgp->qo->custom = custom;
			qp->custom = custom;
			if (custom) cout << "Custom malloc is enabled" << endl;
			else cout << "Custom malloc is disabled" << endl;			
		} else {
			exit = true;
		}

		cout << endl;
		cout << "Cumulated Time: " << time << endl;
		cout << "Execution time: " << execution_time << endl;
		cout << endl;

	}

}
