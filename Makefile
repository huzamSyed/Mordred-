# CUDA_PATH       ?= /usr/local/cuda
# CUDA_INC_PATH   ?= $(CUDA_PATH)/include
# CUDA_BIN_PATH   ?= $(CUDA_PATH)/bin

# NVCC = nvcc

# #SM_TARGETS   = -gencode=arch=compute_52,code=\"sm_52,compute_52\" 
# # SM_DEF     = -DSM520

# SM_TARGETS   = -gencode=arch=compute_70,code=\"sm_70,compute_70\" 
# SM_DEF     = -DSM700

# #GENCODE_SM50    := -gencode arch=compute_52,code=sm_52
# GENCODE_SM70    := -gencode arch=compute_70,code=sm_70
# GENCODE_FLAGS   := $(GENCODE_SM70)

# #NVCCFLAGS += --std=c++11 $(SM_DEF) -Xptxas="-dlcm=cg -v" -lineinfo -Xcudafe -\# 
# NVCCFLAGS += --std=c++14 $(SM_DEF) -Xptxas="-dlcm=cg -v" -lineinfo -Xcudafe -\# 
# OPENMPFLAGS = -Xcompiler -fopenmp -lgomp

# SRC = src
# BIN = bin
# OBJ = obj
# INC = includes

# CUB_DIR = cub/
# INCLUDES = -I$(CUB_DIR) -I$(CUB_DIR)test -I. -I$(INC)

# CFLAGS = -O3 -march=native -std=c++14 -ffast-math
# LDFLAGS = -ltbb
# CINCLUDES = -I$(INC)
# CXX = clang++

# $(OBJ)/%.o: $(SRC)/%.cu
# 	$(NVCC) -lcurand -lcuda $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(BIN)/%: $(OBJ)/%.o
# 	$(NVCC) -ltbb -lcuda $(SM_TARGETS) -lcurand $^ -o $@

# $(OBJ)/cpu/%.o: $(SRC)/cpu/%.cpp
# 	$(NVCC) -lcurand $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# #$(CXX) $(CFLAGS) $(CINCLUDES) -c $< -o $@

# $(BIN)/cpu/%: $(OBJ)/cpu/%.o
# 	$(NVCC) -ltbb $(SM_TARGETS) -lcurand $^ -o $@
	
# #$(CXX) -ltbb $^ -o $@

# $(OBJ)/%.o: $(SRC)/%.cpp
# 	$(NVCC) -lcurand -lcuda $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(OBJ)/gpudb/CostModel.o: $(SRC)/gpudb/CostModel.cu
# 	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(OBJ)/gpudb/QueryOptimizer.o: $(SRC)/gpudb/QueryOptimizer.cu
# 	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(OBJ)/gpudb/QueryProcessing.o: $(SRC)/gpudb/QueryProcessing.cu
# 	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(OBJ)/gpudb/CPUGPUProcessing.o: $(SRC)/gpudb/CPUGPUProcessing.cu
# 	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(OBJ)/gpudb/CPUProcessing.o: $(SRC)/gpudb/CPUProcessing.cu
# 	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(OBJ)/gpudb/main.o: $(SRC)/gpudb/main.cu
# 	$(NVCC) -lcurand -lcuda -ltbb $(SM_TARGETS) $(NVCCFLAGS) $(CPU_ARCH) $(INCLUDES) $(LIBS) -O3 -dc $< -o $@

# $(BIN)/gpudb/main: $(OBJ)/gpudb/main.o $(OBJ)/gpudb/CacheManager.o $(OBJ)/gpudb/QueryOptimizer.o $(OBJ)/gpudb/CPUProcessing.o $(OBJ)/gpudb/CPUGPUProcessing.o $(OBJ)/gpudb/QueryProcessing.o $(OBJ)/gpudb/CostModel.o
# 	$(NVCC) $(SM_TARGETS) -lcuda -ltbb -lcurand $^ -o $@

# setup:
# 	mkdir -p bin/ssb obj/ssb
# 	mkdir -p bin/ops obj/ops
# 	mkdir -p bin/cpu/ssb obj/cpu/ssb
# 	mkdir -p bin/gpudb obj/gpudb

# clean:
# 	rm -rf bin/* obj/*
# =========================
# CUDA paths & toolchain
# =========================
CUDA_PATH       ?= /usr/local/cuda
CUDA_INC_PATH   ?= $(CUDA_PATH)/include
CUDA_BIN_PATH   ?= $(CUDA_PATH)/bin

NVCC            := nvcc

# =========================
# SM / arch targets
# (switch if you need a different GPU)
# =========================
#SM_TARGETS   = -gencode=arch=compute_52,code=\"sm_52,compute_52\"
#SM_DEF       = -DSM520

SM_TARGETS      = -gencode=arch=compute_80,code=\"sm_80,compute_80\"
SM_DEF          = -DSM800

# =========================
# Project layout
# =========================
SRC             := src
BIN             := bin
OBJ             := obj
INC             := includes

CUB_DIR         := cub/
INCLUDES        := -I$(CUB_DIR) -I$(CUB_DIR)test -I. -I$(INC)

# =========================
# Build type toggle
#   make            -> Release (default)
#   make DEBUG=1    -> Debug (host symbols, no device -G)
# =========================
DEBUG ?= 0

# Use all cores by default for parallel builds (you can override by invoking make -jN)
MAKEFLAGS += -j$(shell nproc)

# Use ccache for nvcc when available (speeds repeated builds)
CCACHE := $(shell which ccache 2>/dev/null)
ifeq ($(CCACHE),)
  NVCC := nvcc
else
  NVCC := $(CCACHE) nvcc
endif

NVCC_STD    := --std=c++17
HOST_WARN   := -Xcompiler -Wall -Xcompiler -Wextra
FRAMEPTR    := -Xcompiler -fno-omit-frame-pointer

ifeq ($(DEBUG),1)
  BUILD_TAG   := Debug
  NVCC_MODE   := -Xcompiler -O0 -g $(FRAMEPTR) -DDEBUG
  C_MODE      := -O0 -g -fno-omit-frame-pointer -DDEBUG
  LINK_DBG    := -g
else
  BUILD_TAG   := Release
  NVCC_MODE   := -Xcompiler -O3 -DNDEBUG
  C_MODE      := -O3 -ffast-math -DNDEBUG
  LINK_DBG    :=
endif

# =========================
# Global flags
# =========================
# Keep line info for better backtraces; do NOT add -G (device debug) -> we use gdb only.
NVCCFLAGS   += $(NVCC_STD) $(SM_DEF) -Xptxas="-dlcm=cg -v" -lineinfo -Xcudafe -\# \
               $(HOST_WARN) $(NVCC_MODE)

CFLAGS      := $(C_MODE) -march=native -std=c++17
LDFLAGS     :=
LIBS_COMMON := -ltbb
LIBS_CUDA   := -lcuda -lcurand

# =========================
# Phony/meta targets
# =========================
.PHONY: all setup clean debug release

all: setup $(BIN)/gpudb/main

debug:
	$(MAKE) DEBUG=1 all

release:
	$(MAKE) DEBUG=0 all

# =========================
# Build rules
# =========================
$(OBJ)/%.o: $(SRC)/%.cu
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

$(OBJ)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

# Specialized objects (keep if you want them explicit)
$(OBJ)/gpudb/CostModel.o: $(SRC)/gpudb/CostModel.cu
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

$(OBJ)/gpudb/QueryOptimizer.o: $(SRC)/gpudb/QueryOptimizer.cu
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

$(OBJ)/gpudb/QueryProcessing.o: $(SRC)/gpudb/QueryProcessing.cu
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

$(OBJ)/gpudb/CPUGPUProcessing.o: $(SRC)/gpudb/CPUGPUProcessing.cu
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

$(OBJ)/gpudb/CPUProcessing.o: $(SRC)/gpudb/CPUProcessing.cu
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

$(OBJ)/gpudb/main.o: $(SRC)/gpudb/main.cu
	@mkdir -p $(dir $@)
	$(NVCC) $(SM_TARGETS) $(NVCCFLAGS) $(INCLUDES) -dc $< -o $@

# =========================
# Link rules
# =========================
$(BIN)/%: $(OBJ)/%.o
	@mkdir -p $(dir $@)
	$(NVCC) $(LINK_DBG) $(SM_TARGETS) $^ $(LIBS_CUDA) $(LIBS_COMMON) -o $@

$(BIN)/cpu/%: $(OBJ)/cpu/%.o
	@mkdir -p $(dir $@)
	$(NVCC) $(LINK_DBG) $(SM_TARGETS) $^ $(LIBS_COMMON) -lcurand -o $@

$(BIN)/gpudb/main: \
  $(OBJ)/gpudb/main.o \
  $(OBJ)/gpudb/CacheManager.o \
  $(OBJ)/gpudb/QueryOptimizer.o \
  $(OBJ)/gpudb/CPUProcessing.o \
  $(OBJ)/gpudb/CPUGPUProcessing.o \
  $(OBJ)/gpudb/QueryProcessing.o \
  $(OBJ)/gpudb/CostModel.o
	@mkdir -p $(dir $@)
	$(NVCC) $(LINK_DBG) $(SM_TARGETS) $^ $(LIBS_CUDA) $(LIBS_COMMON) -o $@

# =========================
# Utilities
# =========================
setup:
	mkdir -p bin/ssb obj/ssb
	mkdir -p bin/ops obj/ops
	mkdir -p bin/cpu/ssb obj/cpu/ssb
	mkdir -p bin/gpudb obj/gpudb

clean:
	rm -rf bin/* obj/*
