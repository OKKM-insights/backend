from DataTypes import ImageObject_bb, Labeller, Label, Image, ImageClassMeasure
import numpy as np
import pandas as pd
from ImageClassMeasureDatabaseConnector import ImageClassMeasureDatabaseConnector, MYSQLImageClassMeasureDatabaseConnector
from scipy.special import beta
from collections import deque
from LabellerDatabaseConnector import LabellerDatabaseConnector
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import matplotlib.pyplot as plt


class ObjectExtractionService:

    # generates a list of ImageObjects which have likelihoods over a certain amount

    def __init__(self, icm_db: ImageClassMeasureDatabaseConnector, labeller_db: LabellerDatabaseConnector, threshold: float=.7):
        self.threshold = threshold
        self.icm_db = icm_db
        self.labeller_db = labeller_db

    def get_objects(self, image: Image, Class: str, labellers: list[Labeller], labels: list[Label]) -> list[ImageObject_bb]:
        # get objects for a given image and class
        image_data = np.asarray(image.image_data)

        labellers = pd.DataFrame([l.__dict__ for l in labellers])
        labels = pd.DataFrame([l.__dict__ for l in labels])

        # labels = labels[labels['Class'] == Class]
        labellers = labellers[labellers['skill']==Class]

        print(labels)
        print(labellers)
        icm = self.__get_icm(image.ImageID, Class)

        if not icm:
            print('creating new ICM')
            icm = ImageClassMeasure(image.ImageID, None, None, None, Class, len(image_data[0]), len(image_data[1]))
        else:
            print('ICM loaded')

        for i, labeller in labellers.iterrows(): 
            print(f'applying label group {i}')
            tmp_labels = labels[labels['LabellerID'] == labeller['LabellerID']]
            self.__cuda_update_label_likelihood(icm, tmp_labels, Labeller(labeller['LabellerID'],
                                                                     labeller['skill'],
                                                                     labeller['alpha'],
                                                                     labeller['beta']
                                                                     ))
        
        print(icm.likelihoods)
        self.__update_label_confidence(icm)

        for i, labeller in labellers.iterrows():
            id = labeller['LabellerID']
            print(f'updating labeller {id}') 
            tmp_labels = labels[labels['LabellerID'] == labeller['LabellerID']]
            l = Labeller(labeller['LabellerID'],
                                                                     labeller['skill'],
                                                                     labeller['alpha'],
                                                                     labeller['beta']
                                                                     )
            self.__cuda_update_labeller_accuracy(icm, tmp_labels, l)
            self.labeller_db.push_labeller(l)
        print(icm.likelihoods)
        groups = self.__find_connected_groups(icm.likelihoods)
        print(f'found {len(groups)} groups')
        output = []
        for group in groups:
            tlx, tly, brx, bry = extract_bounding_box(group)
            print(tlx, tly, brx, bry)
            output.append(ImageObject_bb(None, image.ImageID, Class, 0,  tlx, tly, brx, bry))

        print("updating icm")
        self.icm_db.push_imageclassmeasure_images(icm)
        print("icm updated")
        return output

    def __get_icm(self, imageID: str, Class: str) -> ImageClassMeasure:
        query = f"""
            SELECT * FROM ImageClassMeasure_images Where ImageID = '{imageID}' and Label = '{Class}';
        """
        return self.icm_db.get_imageclassmeasures_images(query)


    def __update_label_likelihood(self, icm: ImageClassMeasure, labels:pd.DataFrame, labeller: Labeller):
    # modifies the probabilities of each pixel being in the class based on a new set of labels made by the same labeler
    # can be ported to GPU if performance requires

        a = labeller.alpha
        b = labeller.beta

        for row in range(icm.im_height):
            for col in range(icm.im_width):
                class_prediction = 0
                for i, label in labels.iterrows():
                    if (col >= label['top_left_x'] + label['offset_x'] and col <= label['bot_right_x'] + label['offset_x'] and row >= label['top_left_y'] + label['offset_y'] and row <= label['bot_right_y'] + label['offset_y']):
                        class_prediction = 1
                icm.helper_values[row][col][0] *= beta(1-class_prediction + a, class_prediction + b)
                icm.helper_values[row][col][1] *= beta(class_prediction + a, 1-class_prediction + b)
                icm.likelihoods[row][col] = icm.helper_values[row][col][1] / (icm.helper_values[row][col][1] + icm.helper_values[row][col][0])

    def __cuda_update_label_likelihood(self, icm: ImageClassMeasure, labels:pd.DataFrame, labeller: Labeller):
        mod = SourceModule("""
                           #define CUDA_PRINTF
            struct Small_Label {
                int top_left_x;
                int top_left_y;
                int bot_right_x;
                int bot_right_y;
            };
            __global__ void update_likelihoods(double* likelihoods, double* helper_value_1, 
                                   double* helper_value_2, bool* predictions, 
                                   double alpha, double beta, int im_x, int im_y)
                {
                    int index = blockIdx.x * blockDim.x + threadIdx.x;
                    if (index >= im_x * im_y) return;  // Ensure valid index

                    float prediction = predictions[index] ? 1.0f : 0.0f;

                    double log_gamma_3 = lgamma(fmax(1 + alpha + beta, 1e-9));

                    

                    helper_value_1[index] *= exp(lgamma(fmax(1 - prediction + alpha, 1e-9)) + lgamma(fmax(prediction + beta, 1e-9)) - log_gamma_3);
                    helper_value_2[index] *= exp(lgamma(fmax(prediction + alpha, 1e-9)) + lgamma(fmax(1 - prediction + beta, 1e-9)) - log_gamma_3);

                    double denominator = helper_value_1[index] + helper_value_2[index] + 1e-9;  
                    likelihoods[index] = helper_value_2[index] / denominator;

                    // Debugging: Print some values
                    //if (index % 1000 == 0) {
                    //    printf("Index %d: helper_1=%f, helper_2=%f, likelihood=%f\\n", 
                    //        index, helper_value_1[index], helper_value_2[index], likelihoods[index]);
                    //}
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
        """)
        update_likelihoods = mod.get_function("update_likelihoods")
        mark_predictions = mod.get_function("mark_predictions")

        Small_Label_dtype = np.dtype([('top_left_x', np.int32),
                              ('top_left_y', np.int32),
                              ('bot_right_x', np.int32),
                              ('bot_right_y', np.int32)])
        small_labels = np.empty(len(labels), dtype=Small_Label_dtype)
        for i, label in labels.iterrows():
            small_labels[i] = (label['top_left_x']+label['offset_x'],
                                label['top_left_y']+label['offset_y'],
                                label['bot_right_x']+label['offset_x'],
                                label['bot_right_y']+label['offset_y'])
            
        helper_values_1 = [[pixel[0] for pixel in row] for row in icm.helper_values]
        helper_values_2 = [[pixel[1] for pixel in row] for row in icm.helper_values]

        d_labels = cuda.mem_alloc(small_labels.nbytes)
        size = icm.im_width*icm.im_height
        d_predictions = cuda.mem_alloc(size * np.bool8().itemsize)  # Boolean predictions array
        d_likelihoods = cuda.mem_alloc(size * np.float64().itemsize)  # Likelihoods array
        d_helper_value_1 = cuda.mem_alloc(size * np.float64().itemsize)  # Helper value 1
        d_helper_value_2 = cuda.mem_alloc(size * np.float64().itemsize)  # Helper value 2

        cuda.memcpy_htod(d_likelihoods, np.ascontiguousarray(icm.likelihoods, dtype=np.float64).ravel())
        cuda.memcpy_htod(d_helper_value_1, np.ascontiguousarray(helper_values_1, dtype=np.float64).ravel())
        cuda.memcpy_htod(d_helper_value_2, np.ascontiguousarray(helper_values_2, dtype=np.float64).ravel())
        cuda.memcpy_htod(d_labels, small_labels)
        cuda.memset_d8(d_predictions, 0, size * np.bool8().itemsize)

        block_size = 256
        num_blocks = (len(labels) + block_size - 1) // block_size

        mark_predictions(d_predictions, d_labels, np.int32(len(labels)), np.int32(icm.im_width), np.int32(icm.im_height),
                     block=(block_size, 1, 1), grid=(num_blocks, 1))
        cuda.Context.synchronize()


        alpha = labeller.alpha
        beta = labeller.beta


        num_blocks = (icm.im_height*icm.im_width + block_size - 1) // block_size
        update_likelihoods(d_likelihoods, d_helper_value_1, d_helper_value_2, d_predictions, 
                       np.float64(alpha), np.float64(beta), np.int32(icm.im_width), np.int32(icm.im_height),
                       block=(block_size, 1, 1), grid=(num_blocks, 1))
        cuda.Context.synchronize()

        likelihoods = np.empty(size, dtype=np.float64)
        helper_value_1 = np.empty(size, dtype=np.float64)
        helper_value_2 = np.empty(size, dtype=np.float64)
        preds = np.empty(size, dtype=np.bool8)

        cuda.memcpy_dtoh(likelihoods, d_likelihoods)
        cuda.memcpy_dtoh(helper_value_1, d_helper_value_1)
        cuda.memcpy_dtoh(helper_value_2, d_helper_value_2)
        cuda.memcpy_dtoh(preds, d_predictions)

        print("First 10 likelihood values after CUDA execution:", likelihoods[:10])
        icm.likelihoods = likelihoods.reshape(icm.im_width, icm.im_height)
        icm.helper_values = np.stack((helper_value_1.reshape(icm.im_width, icm.im_height), helper_value_2.reshape(icm.im_width, icm.im_height)), axis=-1)

        plt.imshow(icm.likelihoods)
        plt.colorbar()
        plt.savefig('temp.jpeg')
        print(sum(preds)) 

        d_predictions.free()
        d_likelihoods.free()
        d_helper_value_1.free()
        d_helper_value_2.free()
        d_labels.free()



    def __update_label_confidence(self, icm: ImageClassMeasure):
        for row in range(icm.im_height):
            for col in range(icm.im_width):
                prediction = 1 if icm.likelihoods[row][col] > self.threshold else 0
                icm.confidence[row][col] = abs(icm.likelihoods[row][col] - 1 + prediction)

    def __cuda_update_label_confidence(self, icm: ImageClassMeasure):
        mod = SourceModule("""
            __global__ void update_confidence(double* likelihoods, double* confidence, 
                                                double threshold, int im_x, int im_y)
            {
                int index = blockIdx.x * blockDim.x + threadIdx.x;
                if (index < im_x * im_y) {
                    confidence[index] = abs(likelihoods[index]-1 + (likelihoods[index] > threshold));
                }
            }
                           
        """)

    def __update_labeler_accuracy(self, icm: ImageClassMeasure, labels:pd.DataFrame, labeller: Labeller):
        # update agent accuracy based on proportion of pixels correctly labeled
        image_size = icm.im_height * icm.im_width
        a:float = 0
        b:float = 0

        for row in range(icm.im_height):
            for col in range(icm.im_width):
                class_prediction = 1 if icm.likelihoods[row][col] > self.threshold else 0
                label_prediction = 0
                for i, label in labels.iterrows():
                    if (col >= label['top_left_x'] + label['offset_x'] and col <= label['bot_right_x'] + label['offset_x'] and row >= label['top_left_y'] + label['offset_y'] and row <= label['bot_right_y'] + label['offset_y']):
                        label_prediction = 1
                        break
                if class_prediction == label_prediction:
                    a += icm.confidence[row][col]
                else:
                    b += icm.confidence[row][col]
        
        labeller.alpha += a/image_size
        labeller.beta += b/image_size

    def __cuda_update_labeller_accuracy(self, icm: ImageClassMeasure, labels:pd.DataFrame, labeller: Labeller):
        mod = SourceModule("""
                           #define CUDA_PRINTF
            struct Small_Label {
                int top_left_x;
                int top_left_y;
                int bot_right_x;
                int bot_right_y;
            };
                           
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
        """)
        mark_predictions = mod.get_function("mark_predictions")

        Small_Label_dtype = np.dtype([('top_left_x', np.int32),
                              ('top_left_y', np.int32),
                              ('bot_right_x', np.int32),
                              ('bot_right_y', np.int32)])
        small_labels = np.empty(len(labels), dtype=Small_Label_dtype)
        for i, label in labels.iterrows():
            small_labels[i] = (label['top_left_x']+label['offset_x'],
                                label['top_left_y']+label['offset_y'],
                                label['bot_right_x']+label['offset_x'],
                                label['bot_right_y']+label['offset_y'])

        d_labels = cuda.mem_alloc(small_labels.nbytes)
        
        size = icm.im_width*icm.im_height
        d_predictions = cuda.mem_alloc(size * np.bool8().itemsize)  # Boolean predictions array
        cuda.memcpy_htod(d_labels, small_labels)
        cuda.memset_d8(d_predictions, 0, size * np.bool8().itemsize)

        block_size = 256
        num_blocks = (len(labels) + block_size - 1) // block_size

        mark_predictions(d_predictions, d_labels, np.int32(len(labels)), np.int32(icm.im_width), np.int32(icm.im_height),
                     block=(block_size, 1, 1), grid=(num_blocks, 1))
        cuda.Context.synchronize()
        



        preds = np.empty(size, dtype=np.bool8)
        cuda.memcpy_dtoh(preds, d_predictions)
        preds = preds.reshape(icm.im_width, icm.im_height)

        d_predictions.free()
        d_labels.free()


        a:float = 0
        b:float = 0
        image_size = icm.im_height * icm.im_width
        miss_count = 0
        for row in range(icm.im_height):
            for col in range(icm.im_width):
                class_prediction = 1 if icm.likelihoods[row][col] > self.threshold else 0
                if class_prediction == preds[row][col]:
                    a += icm.confidence[row][col]
                else:
                    miss_count += 1
                    b += icm.confidence[row][col]
        
        labeller.alpha += a/image_size
        labeller.beta += b/image_size

        print(miss_count)
        print(labeller.alpha, labeller.beta)




    def __find_connected_groups(self, grid):
        """
        Identifies all groups of connected pixels above a given threshold.

        :param grid: 2D list of numerical values
        :param threshold: Minimum value for a pixel to be included in a group
        :return: List of groups, where each group is a list of (x, y) coordinates
        """
        print(grid)
        # if not grid or not grid[0]:  # Handle empty input
        #     return []

        rows, cols = len(grid), len(grid[0])
        visited = set()  # Keep track of visited pixels
        groups = []  # List to store all groups

        # 8 possible directions (up, down, left, right, diagonals)
        directions = [(-1, -1), (-1, 0), (-1, 1),
                    (0, -1),         (0, 1),
                    (1, -1), (1, 0), (1, 1)]

        def __bfs(start_x, start_y):
            """Performs BFS to find all connected pixels in a group."""
            queue = deque([(start_x, start_y)])
            group = []  # Store (x, y) positions of the current group
            visited.add((start_x, start_y))

            while queue:
                x, y = queue.popleft()
                group.append((x, y))

                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in visited:
                        if grid[nx][ny] > self.threshold:
                            queue.append((nx, ny))
                            visited.add((nx, ny))

            return group

        # Iterate through the grid
        for i in range(rows):
            for j in range(cols):
                if grid[i][j] > self.threshold and (i, j) not in visited:
                    groups.append(__bfs(i, j))

        return groups

def extract_bounding_box(pixels):
    # Convert list of pixels to a numpy array for efficient computation
    pixels_np = np.array(pixels)
    
    # Extract x and y coordinates
    x_coords = pixels_np[:, 0]
    y_coords = pixels_np[:, 1]
    
    # Calculate the bounding box
    top_left_x = np.min(x_coords)
    top_left_y = np.min(y_coords)
    bot_right_x = np.max(x_coords)
    bot_right_y = np.max(y_coords)
    
    return top_left_x, top_left_y, bot_right_x, bot_right_y
# o = ObjectExtractionService()
# i = Image('1','2','1')
# ls = [Labeller('t', 'boat','1.1','1.2'),
#       Labeller('2', 'boat','1.3','1.2')]
# o.get_objects(i, ls, None)