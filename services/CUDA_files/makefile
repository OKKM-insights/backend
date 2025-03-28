# Compiler
NVCC = nvcc

# Compiler flags
CFLAGS = -O2 -arch=sm_60 -Xcompiler -fPIC

# Linker flags for creating a shared library
LINKER_FLAGS = -shared

# Source files (your .cu files)
SRC = main.cu kernels.cu
OBJ = $(SRC:.cu=.o)

# Output shared library (adjust file name as needed)
TARGET = libcalculate_label_likelihood.so

# Default target
all: $(TARGET)

# Compile .cu files to object files (.o)
%.o: %.cu
	$(NVCC) $(CFLAGS) -c $< -o $@

# Link object files into a shared library
$(TARGET): $(OBJ)
	$(NVCC) $(LINKER_FLAGS) $(OBJ) -o $(TARGET)

# Clean up generated files
clean:
	rm -f $(TARGET) $(OBJ)
