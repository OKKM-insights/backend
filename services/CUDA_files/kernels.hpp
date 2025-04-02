#ifndef KERNELS_HPP
#define KERNELS_HPP

#include "small_label.hpp"


__global__ void mark_predictions(bool* d_predictions, Small_Label* d_labels, int num_labels, int im_x, int im_y);
__global__ void update_likelihoods(double* likelihoods, double* helper_value_1, double* helper_value_2, bool* predictions, double alpha, double beta, int im_x, int im_y);
extern "C" void launch_update_likelihoods(
    double* d_likelihoods, 
    double* d_helper_value_1, 
    double* d_helper_value_2, 
    bool* d_predictions, 
    double alpha, 
    double beta, 
    int im_x, 
    int im_y
);
extern "C" void launch_mark_predictions(
    bool* d_predictions, 
    Small_Label* d_labels, 
    int num_labels, 
    int im_x, 
    int im_y
);
#endif
