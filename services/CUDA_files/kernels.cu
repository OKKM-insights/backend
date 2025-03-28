#include <iostream>
#include <cuda_runtime.h>
#include "small_label.hpp"

extern "C" {  // Ensure these functions are exposed for C linkage

__global__ void update_likelihoods(
    double* likelihoods, 
    double* helper_value_1, 
    double* helper_value_2, 
    bool* predictions, 
    double alpha, 
    double beta, 
    int im_x, 
    int im_y)
{
    int index = blockIdx.x * blockDim.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;

    for(int i = index; i < im_x * im_y; i += stride){
        bool prediction = predictions[i];
        helper_value_1[i] *= tgamma(1-prediction+alpha) * tgamma(prediction+beta) / tgamma(1 + alpha + beta);
        helper_value_2[i] *= tgamma(prediction+alpha) * tgamma(1-prediction+beta) / tgamma(1 + alpha + beta);
        likelihoods[i] = helper_value_1[i] / (helper_value_1[i] + helper_value_2[i]);
    }
}

__global__ void mark_predictions(bool* d_predictions, Small_Label* d_labels, int num_labels, int im_x, int im_y) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= num_labels) return;

    Small_Label l = d_labels[idx];

    for (int row = l.top_left_y; row <= l.bot_right_y; row++) {
        for (int col = l.top_left_x; col <= l.bot_right_x; col++) {
            d_predictions[row * im_x + col] = true;
        }
    }
}

// Export function to launch kernels
extern "C" void launch_update_likelihoods(
    double* d_likelihoods, 
    double* d_helper_value_1, 
    double* d_helper_value_2, 
    bool* d_predictions, 
    double alpha, 
    double beta, 
    int im_x, 
    int im_y
) {
    int blockSize = 256;
    int numBlocks = (im_x * im_y + blockSize - 1) / blockSize;
    update_likelihoods<<<numBlocks, blockSize>>>(d_likelihoods, d_helper_value_1, d_helper_value_2, d_predictions, alpha, beta, im_x, im_y);
}

extern "C" void launch_mark_predictions(
    bool* d_predictions, 
    Small_Label* d_labels, 
    int num_labels, 
    int im_x, 
    int im_y
) {
    int blockSize = 256;
    int numBlocks = (num_labels + blockSize - 1) / blockSize;
    mark_predictions<<<numBlocks, blockSize>>>(d_predictions, d_labels, num_labels, im_x, im_y);
}
}
