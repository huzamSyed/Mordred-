include config.mk

CUDA_PATH       ?= /opt/cuda
CUDA_INC_PATH   ?= $(CUDA_PATH)/include
CUDA_BIN_PATH   ?= $(CUDA_PATH)/bin

NVCC = $(CUDA_BIN_PATH)/nvcc

#SM_TARGETS   = -gencode=arch=compute_52,code=\"sm_52,compute_52\" 
# SM_DEF     = -DSM520

SM_TARGETS   = -gencode=arch=compute_70,code=\"sm_70,compute_70\" 
SM_DEF     = -DSM700

#GENCODE_SM50    := -gencode arch=compute_52,code=sm_52
GENCODE_SM70    := -gencode arch=compute_70,code=sm_70
GENCODE_FLAGS   := $(GENCODE_SM70)

#NVCCFLAGS += --std=c++11 $(SM_DEF) -Xptxas="-dlcm=cg -v" -lineinfo -Xcudafe -\# 
NVCCFLAGS += --std=c++14 $(SM_DEF) -Xptxas="-dlcm=cg -v" -lineinfo -Xcudafe -\# 
OPENMPFLAGS = -Xcompiler -fopenmp -lgomp

SRC = src
BIN = bin
OBJ = obj
INC = includes

CUB_DIR = cub/
INCLUDES = -I$(CUB_DIR) -I$(CUB_DIR)test -I. -I$(INC)

PREFLAGS = -DMOD_PATH=\"$(MOD_PATH)\" -DSF=$(SF)
PREFLAGS += -DBASE_PATH=\"$(BASE_PATH)\" \
          -DDATA_DIR=\"$(DATA_DIR)\" \
          -DLO_LEN=$(LO_LEN) \
          -DP_LEN=$(P_LEN) \
          -DS_LEN=$(S_LEN) \
          -DC_LEN=$(C_LEN) \
          -DD_LEN=$(D_LEN)

$(OBJ)/%.o: $(SRC)/%.cu
	$(NVCC) -lcurand -lcuda $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(BIN)/%: $(OBJ)/%.o
	$(NVCC) -ltbb -lcuda $(SM_TARGETS) $(PREFLAGS) -lcurand $^ -o $@

$(OBJ)/%.o: $(SRC)/%.cpp
	$(NVCC) -lcurand -lcuda $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(OBJ)/gpudb/CostModel.o: $(SRC)/gpudb/CostModel.cu
	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(OBJ)/gpudb/QueryOptimizer.o: $(SRC)/gpudb/QueryOptimizer.cu
	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(OBJ)/gpudb/QueryProcessing.o: $(SRC)/gpudb/QueryProcessing.cu
	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(OBJ)/gpudb/CPUGPUProcessing.o: $(SRC)/gpudb/CPUGPUProcessing.cu
	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(OBJ)/gpudb/CPUProcessing.o: $(SRC)/gpudb/CPUProcessing.cu
	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(OBJ)/gpudb/main.o: $(SRC)/gpudb/main.cu
	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(PREFLAGS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

$(BIN)/gpudb/main: $(OBJ)/gpudb/main.o $(OBJ)/gpudb/CacheManager.o $(OBJ)/gpudb/QueryOptimizer.o $(OBJ)/gpudb/CPUProcessing.o $(OBJ)/gpudb/CPUGPUProcessing.o $(OBJ)/gpudb/QueryProcessing.o $(OBJ)/gpudb/CostModel.o
	$(NVCC) $(SM_TARGETS) $(PREFLAGS) -lcuda -ltbb -lcurand $^ -o $@

setup:
	mkdir -p bin/gpudb obj/gpudb

clean:
	rm -rf bin/* obj/*
