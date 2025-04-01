#include <cuda_runtime.h>
#include <iostream>
#include "small_label.hpp"
#include "kernels.hpp"




extern "C" {
int calculate_label_likelihood(
    double* d_likelihoods, 
    double* d_helper_value_1, 
    double* d_helper_value_2, 
    double alpha, 
    double beta, 
    Small_Label* labels, 
    int num_labels, 
    int im_x,  // Image width
    int im_y   // Image height
)
{
    int size = im_x * im_y;  // Total number of pixels

    // **Allocate GPU memory for boolean predictions array**
    bool* d_predictions;
    cudaMalloc(&d_predictions, size * sizeof(bool));

    // **Initialize GPU predictions array to false (0)**
    cudaMemset(d_predictions, 0, size * sizeof(bool));

    // **Allocate host-side labels array and copy to GPU**
    Small_Label* d_labels;
    cudaMalloc(&d_labels, num_labels * sizeof(Small_Label));
    cudaMemcpy(d_labels, labels, num_labels * sizeof(Small_Label), cudaMemcpyHostToDevice);

    // **CUDA Kernel: Mark labeled regions in `d_predictions`**
    int blockSize = 256;
    int numBlocks = (num_labels + blockSize - 1) / blockSize;
    mark_predictions<<<numBlocks, blockSize>>>(d_predictions, d_labels, num_labels, im_x, im_y);
    cudaDeviceSynchronize(); // Ensure marking is complete

    // **Launch the likelihood update kernel**

    update_likelihoods<<<numBlocks, blockSize>>>(d_likelihoods, d_helper_value_1, d_helper_value_2, d_predictions, alpha, beta, im_x, im_y);
    cudaDeviceSynchronize(); // Ensure marking is complete

    // **Free device memory**
    cudaFree(d_predictions);
    cudaFree(d_labels);

    return 0; // Success
}

int main(){
    return 0;
}

}