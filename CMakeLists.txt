cmake_minimum_required(VERSION 3.22)
project(GPUDatabase LANGUAGES CXX CUDA)

include("${CMAKE_SOURCE_DIR}/config.cmake")

find_package(CUDA REQUIRED)

# --- Project directories ---
set(SRC "${CMAKE_SOURCE_DIR}/src")
set(INC "${CMAKE_SOURCE_DIR}/includes")
set(CYRS "${CMAKE_SOURCE_DIR}/crystal")
set(OBJ "${CMAKE_BINARY_DIR}/obj")
set(BIN "${CMAKE_SOURCE_DIR}/bin")
set(CUB_DIR "${CMAKE_SOURCE_DIR}/cub")

file(MAKE_DIRECTORY "${BIN}" "${BIN}/gpudb" "${OBJ}/gpudb")

# --- Source files ---
set(GPUSOURCES
    ${SRC}/gpudb/main.cu
    ${SRC}/gpudb/CacheManager.cu
    ${SRC}/gpudb/QueryOptimizer.cu
    ${SRC}/gpudb/CPUProcessing.cu
    ${SRC}/gpudb/CPUGPUProcessing.cu
    ${SRC}/gpudb/QueryProcessing.cu
    ${SRC}/gpudb/CostModel.cu
)

# --- CUDA architecture (SM flags) ---
set(GENCODE_FLAGS "-gencode=arch=compute_70,code=sm_70")
set(SM_DEF "-DSM700")

# --- Compile options ---
set(NVCC_FLAGS
    "-Xptxas=-dlcm=cg;-v"
    -lineinfo
    "-Xcudafe=--display_error_number"
)

set(OPENMP_FLAGS "-Xcompiler=-fopenmp")
set(LINK_LIBS tbb cuda curand gomp)

# --- Include directories ---
include_directories(
    ${INC}
    ${CUB_DIR}
    ${CUB_DIR}/test
    ${CMAKE_SOURCE_DIR}
)

# --- Preprocessor definitions from config.mk ---
add_compile_definitions(
    MOD_PATH="${MOD_PATH}"
    SF=${SF}
    BASE_PATH="${BASE_PATH}"
    DATA_DIR="${DATA_DIR}"
    LO_LEN=${LO_LEN}
    P_LEN=${P_LEN}
    S_LEN=${S_LEN}
    C_LEN=${C_LEN}
    D_LEN=${D_LEN}
)

# --- Target ---
add_executable(main ${GPUSOURCES})
set_target_properties(main PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${BIN}/gpudb"
    CUDA_ARCHITECTURES native
    CUDA_SEPARABLE_COMPILATION ON
)
target_compile_definitions(main PRIVATE
    MOD_PATH="${MOD_PATH}"
    SF=${SF}
    BASE_PATH="${BASE_PATH}"
    DATA_DIR="${DATA_DIR}"
    LO_LEN=${LO_LEN}
    P_LEN=${P_LEN}
    S_LEN=${S_LEN}
    C_LEN=${C_LEN}
    D_LEN=${D_LEN}
)
target_compile_options(main PRIVATE ${NVCC_FLAGS} ${OPENMP_FLAGS})
target_link_libraries(main PRIVATE ${LINK_LIBS})

set(TESTSOURCES
    ${SRC}/gpudb/test.cu
    ${SRC}/gpudb/CacheManager.cu
    ${SRC}/gpudb/QueryOptimizer.cu
    ${SRC}/gpudb/CPUProcessing.cu
    ${SRC}/gpudb/CPUGPUProcessing.cu
    ${SRC}/gpudb/QueryProcessing.cu
    ${SRC}/gpudb/CostModel.cu
)

add_executable(test ${TESTSOURCES})
set_target_properties(test PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${BIN}/gpudb"
    CUDA_ARCHITECTURES native
    CUDA_SEPARABLE_COMPILATION ON
)
target_compile_definitions(test PRIVATE
    MOD_PATH="${MOD_PATH}"
    SF=${SF}
    BASE_PATH="${BASE_PATH}"
    DATA_DIR="${DATA_DIR}"
    LO_LEN=${LO_LEN}
    P_LEN=${P_LEN}
    S_LEN=${S_LEN}
    C_LEN=${C_LEN}
    D_LEN=${D_LEN}
)
target_compile_options(test PRIVATE ${NVCC_FLAGS} ${OPENMP_FLAGS})
target_link_libraries(test PRIVATE ${LINK_LIBS})

set(MINMAX_SOURCES
    ${SRC}/gpudb/minmax.cpp
)
add_executable(minmax ${MINMAX_SOURCES})
set_target_properties(minmax PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${BIN}/gpudb"
)

set(MINMAXSORT_SOURCES
    ${SRC}/gpudb/minmaxsort.cpp
)
add_executable(minmaxsort ${MINMAXSORT_SOURCES})
set_target_properties(minmaxsort PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${BIN}/gpudb"
)

message(STATUS "Configured with:")
message(STATUS "  MOD_PATH=${MOD_PATH}")
message(STATUS "  SF=${SF}")
message(STATUS "  BASE_PATH=${BASE_PATH}")
message(STATUS "  DATA_DIR=${DATA_DIR}")
